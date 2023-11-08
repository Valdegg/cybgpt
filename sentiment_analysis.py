from langchain.chat_models import ChatOpenAI
from langchain import ConversationChain
from langchain.callbacks.manager import AsyncCallbackManager
import json 
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain.schema import SystemMessage
from langchain.memory import ConversationBufferMemory




with open("system_prompts.json", "r") as system_messages_file:
    system_messages = json.load(system_messages_file)


def get_sent_chain(stream_handler, tracing: bool = False) -> ConversationChain:
    """Create a ConversationChain for question/answering."""
    prompt = ChatPromptTemplate.from_messages(
       [
          SystemMessage(content=system_messages["detect_negative_or_positive_sentiment_revised"]),
          MessagesPlaceholder(variable_name="history"),
          HumanMessagePromptTemplate.from_template("{input}"),

       ]
     )
    manager = AsyncCallbackManager([])
    stream_manager = AsyncCallbackManager([stream_handler])
    llm_sales_rep = ChatOpenAI(model="gpt-4", streaming=True, callback_manager=stream_manager, verbose=True)

    memory = ConversationBufferMemory(return_messages=True)

    sentiment_analysis_chain = ConversationChain(
        callback_manager=manager, memory=memory, llm=llm_sales_rep, verbose=True, prompt=prompt
    )

    return sentiment_analysis_chain

