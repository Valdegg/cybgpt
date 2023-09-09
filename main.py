import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from schemas import ChatResponse
from callback import StreamingLLMCallbackHandler
from websockets.exceptions import ConnectionClosedOK
from create_chains import get_wiener_chain
import logging
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)



app = FastAPI()

origins = [
    "https://www.clubofremy.org/",
    "http://localhost",
    "http://localhost:8080",
    "https://gpt-thor.ngrok.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#####################################################
SELECTED_PERSONA = "wiener"
##########################################################################

# Load the environment variables from the .env file
load_dotenv()

# Access the variables using os.environ
openai_api_key = os.environ.get("OPENAI_API_KEY")

templates = Jinja2Templates(directory="templates")



cybernetician_images = {
    "claude_shannon": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Claude_Shannon.jpg",
    "ernst_von_glasersfeld": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Ernst_von_Glasersfeld.jpg",
    "gordon_pask": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Gordon_Pask.gif",
    "gregory_bateson": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Gregory_Bateson.jpg",
    "heinz_von_foerster": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Heinz_von_Foerster.jpg",
    "hsue_shen_tsien": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Hsue-Shen_Tsien.jpg",
    "humberto_maturana": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Humberto_Maturana.jpg",
    "john_von_neumann": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/John_von_Neumann.gif",
    "norbert_wiener": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Norbert_Wiener.jpg",
    "russell_ackoff": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Russell_Ackoff.jpg",
    "stafford_beer": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Stafford_Beer.jpg",
    "w_ross_ashby": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/W_Ross_Ashby.jpg",
    "walter_cannon": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Walter_Cannon.jpg",
    "warren_s_mcculloch": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Warren_S_McCulloch.png",
    "warren_weaver": "/home/valdegg/Documents/ai_projects/cyb_gpt/wiki_images/Warren_Weaver.jpg",
}

@app.get("/cybernetician/{cybernetician_id}")
async def read_item(cybernetician_id: str):
    image_path = cybernetician_images.get(cybernetician_id)
    if image_path:
        return FileResponse(image_path)
    else:
        return {"error": "Image not found"}

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test")
async def test_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ping/{persona_selected_from_dropdown}")
async def ping(persona_selected_from_dropdown):
    return {"ping": persona_selected_from_dropdown}

@app.websocket("/ws/{persona_selected_from_dropdown}")
async def websocket_endpoint(websocket: WebSocket, persona_selected_from_dropdown):
    logger.info('Websocket connection opened')
    await websocket.accept()
    stream_handler = StreamingLLMCallbackHandler(websocket)
    print(persona_selected_from_dropdown)
    cyber_chain = get_wiener_chain(stream_handler, selected_persona=persona_selected_from_dropdown    )
    logger.info('Chain loaded')
    while True:
        try:
            # Receive and send back the client message
            logger.info('Waiting for message')
            user_msg = await websocket.receive_text()
            resp = ChatResponse(sender="human", message=user_msg, type="stream")
            logger.info('Received message')
            await websocket.send_json(resp.dict())

            # Construct a response
            start_resp = ChatResponse(sender="bot", message="", type="start")  
            await websocket.send_json(start_resp.dict())

            # Send the message to the chain and feed the response back to the client
            output = await cyber_chain.acall(
                {
                    "input": user_msg,
                }
            )
            logger.info(output)
            # Send the end-response back to the client
            end_resp = ChatResponse(sender="bot", message="", type="end")
            print(end_resp)
            await websocket.send_json(end_resp.dict())
            # save answer to txt file
            with open('answer.txt', 'w') as f:
                f.write(end_resp.message)
            # log answer 
            logger.info(end_resp.message)
        except WebSocketDisconnect:
            logger.info("WebSocketDisconnect")
            # TODO try to reconnect with back-off
            break
        except ConnectionClosedOK:
            logger.info("ConnectionClosedOK")
            # TODO handle this?
            break
        except Exception as e:
            logging.error(e)
            resp = ChatResponse(
                sender="bot",
                message="Sorry, something went wrong. Try again.",
                type="error",
            )
            await websocket.send_json(resp.dict())
