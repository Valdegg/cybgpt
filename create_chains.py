"""Create a ChatVectorDBChain for question/answering."""
from langchain import ConversationChain
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.callbacks.tracers import LangChainTracer
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.chat_vector_db.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import json

selected_personae = "Norbert Wiener"
# open wiki_article_ + selected_personae.json
with open("wiki_article_" + selected_personae + ".txt", "r") as wiener_file:
    wiener_page = wiener_file.read()


selected_personae = "Stafford Beer"
# open wiki_article_ + selected_personae.json
with open("wiki_article_" + selected_personae + ".txt", "r") as beer_file:
    beer_page = beer_file.read()

with open("system_prompts.json", "r") as system_messages_file:
    system_messages = json.load(system_messages_file)

def get_wiener_chain(stream_handler, selected_persona, tracing: bool = False) -> ConversationChain:
    """Create a ConversationChain for question/answering."""

    wiener_intro_prompt = system_messages['personae'][selected_persona]["intro"] + wiener_page.replace('{', '(').replace('}', ')') + '\n\n End of wikipedia page. \n\n'
    print(wiener_intro_prompt)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                wiener_intro_prompt
            ),
            SystemMessagePromptTemplate.from_template(
                system_messages['personae'][selected_persona]["student"]
            ),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )
    manager = AsyncCallbackManager([])
    stream_manager = AsyncCallbackManager([stream_handler])
    if tracing:
        tracer = LangChainTracer()
        tracer.load_default_session()
        manager.add_handler(tracer)
        stream_manager.add_handler(tracer)

    streaming_llm = ChatOpenAI(
        model = 'gpt-4',
        streaming=True,
        callback_manager=stream_manager,
        verbose=True,
        temperature=0,
    )

    memory = ConversationBufferMemory(return_messages=True)

    qa = ConversationChain(
        callback_manager=manager, memory=memory, llm=streaming_llm, verbose=True, prompt=prompt
    )

    return qa



def get_beer_chain(stream_handler, tracing: bool = False) -> ConversationChain:
    """Create a ConversationChain for question/answering."""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                system_messages["personae"]["beer_intro"] + beer_page + '\n\n End of wikipedia page. \n\n'
            ),
            SystemMessagePromptTemplate.from_template(
                system_messages["personae"]["beer_student"]
            ),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )
    manager = AsyncCallbackManager([])
    stream_manager = AsyncCallbackManager([stream_handler])
    if tracing:
        tracer = LangChainTracer()
        tracer.load_default_session()
        manager.add_handler(tracer)
        stream_manager.add_handler(tracer)

    streaming_llm = OpenAI(
        streaming=True,
        callback_manager=stream_manager,
        verbose=True,
        temperature=0,
    )

    memory = ConversationBufferMemory(return_messages=True)

    qa = ConversationChain(
        callback_manager=manager, memory=memory, llm=streaming_llm, verbose=True, prompt=prompt
    )

    return qa