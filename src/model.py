from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-5.6-terra",
    use_responses_api=True,
)
