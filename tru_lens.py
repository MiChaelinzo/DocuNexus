import boto3

# Initialize Bedrock client
client = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

from langchain import LLMChain
from langchain_aws import ChatBedrock
from langchain.prompts.chat import AIMessagePromptTemplate
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate

bedrock_llm = ChatBedrock(model_id="mistral.mistral-large-2402-v1:0", client=client)

# Set up the prompt templates
template = "You are a helpful assistant."
system_message_prompt = SystemMessagePromptTemplate.from_template(template)
example_human = HumanMessagePromptTemplate.from_template("Hi")
example_ai = AIMessagePromptTemplate.from_template("Argh me mateys")
human_template = "{text}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

chat_prompt = ChatPromptTemplate.from_messages(
    [system_message_prompt, example_human, example_ai, human_message_prompt]
)

# Initialize LLM chain
chain = LLMChain(llm=bedrock_llm, prompt=chat_prompt, verbose=True)

# Run the chain
print(chain.run("Current climate change status"))

from trulens.core import Feedback
from trulens.core import TruSession
from trulens.apps.langchain import TruChain
from trulens.providers.bedrock import Bedrock

session = TruSession()
session.reset_database()

# Initialize Bedrock-based feedback provider class:
bedrock = Bedrock(model_id="mistral.mistral-large-2402-v1:0", region_name="us-east-1")

# Define a feedback function using the Bedrock provider.
f_qa_relevance = Feedback(
    bedrock.relevance_with_cot_reasons, name="Answer Relevance"
).on_input_output()
# By default this will check language match on the main app input and main app
# output.

tru_recorder = TruChain(
    chain, app_name="Chain1_ChatApplication", feedbacks=[f_qa_relevance]
)

with tru_recorder as recording:
    llm_response = chain.run("Tell me about the current wildfires in California & Los angeles?")

display(llm_response)

from trulens.dashboard import run_dashboard

run_dashboard(session)  # open a local streamlit app to explore

# stop_dashboard(session) # stop if needed

session.get_records_and_feedback()[0]