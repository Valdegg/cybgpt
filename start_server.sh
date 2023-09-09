python3 kill_process.py ngrok uvicorn
python3 kill_process.py ngrok uvicorn

sleep 2

# Set the port numbers
uvicorn_port=8001


if [ "$1" == "-online" ]; then

    echo "Starting ngrok"
    ./ngrok http --region=us --hostname=gpt-thor.ngrok.io "$uvicorn_port" > /dev/null &

    # Wait until ngrok tunnel is available
    while [[ -z "$ngrok_tunnel" || "$ngrok_tunnel" == "null" ]]; do
        echo "Waiting for ngrok tunnel..."
        sleep 1.5
        ngrok_tunnel=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    done
    
    echo "ngrok tunnel available at $ngrok_tunnel"
fi 

echo "Starting uvicorn server..."
# Start the API
uvicorn main:app --host 0.0.0.0 --port "$uvicorn_port" --log-config logging_config.ini > server_logs.txt 2>&1 &
#uvicorn api:app --reload &> server_logs.txt&

UVICORN_PID=$!

# Wait until uvicorn server is ready
while ! curl -s "http://localhost:$uvicorn_port" > /dev/null; do
    # Check if the process is still running
    if ! ps -p $UVICORN_PID > /dev/null; then
        echo "Uvicorn process has stopped. Exiting..."
        echo "The last few lines of the server logs are:"
        tail server_logs.txt
        exit 1
    fi
    echo "Waiting for uvicorn server..."
    sleep 4
done



# if $1 != "--online" then we use the hostname to connect to the front-end server, not this one
if [ "$1" != "-online" ]; then
    echo "Running on a local server. To run on a public server, use the -online flag."
 #  ./ngrok http --region=us --hostname=gpt-thor.ngrok.io 3000
    echo "Uvicorn server has been started!"
    echo "at http://localhost:$uvicorn_port"
fi



#npm run dev 
