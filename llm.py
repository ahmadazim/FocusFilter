import asyncio
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import json
import re
from user_preferences import RESEARCH_TOPICS, PREFERRED_AUTHORS, PREFERRED_AFFILIATIONS, USER_RESEARCH_INTERESTS
from openai import OpenAIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential
)

class OpenAIChat:
    model = ChatOpenAI(
        openai_api_key=open('.openai_api_key').read().strip(),
        model_name='gpt-4o'
    )

    @classmethod
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(10))
    async def chat(cls, request):
        response = await asyncio.to_thread(
            cls.model.invoke, [HumanMessage(content=request)]
        )
        response = cls.clean_response(response.content)

        try:
            json_response = json.loads(response)
        except json.JSONDecodeError:
            # Retry with a reminder to format the response as valid JSON
            reminder_request = request + "\n\nPlease ensure the response is in valid JSON format."
            response = await asyncio.to_thread(
                cls.model.invoke, [HumanMessage(content=reminder_request)]
            )
            response = cls.clean_response(response.content)

            try:
                json_response = json.loads(response)
            except json.JSONDecodeError as e:
                print(f"JSONDecodeError after retry: {e} - Response: {response}")
                return {
                    "relevance_score": 0,
                    "thoughts": "Invalid JSON response from LLM after retry.",
                    "summary": "N/A",
                    "relevant_topics": []
                }
        print(json_response)
        return json_response

    @staticmethod
    def clean_response(response):
        response = response.strip().strip('```json').strip('```')
        response = re.sub(r'\\', r'\\\\', response)
        response = re.sub(r'\$', '', response)
        return response

def match_pattern(item, patterns):
    return any(re.search(r'\b' + re.escape(pattern) + r'\b', item, re.IGNORECASE) for pattern in patterns)

def is_preferred_paper(paper_dict):
    return (any(match_pattern(author, PREFERRED_AUTHORS) for author in paper_dict['authors']) or
            any(match_pattern(affiliation, PREFERRED_AFFILIATIONS) for affiliation in paper_dict['affiliations']))

def create_prompt(paper_dict):
    return f"""
    You are a professional research assistant. Please read the title and abstract of the paper I provide below and summarize it into 1-2 sentences. 
    Next, evaluate the relevance of the paper given the user's research topics and interests.
    A paper is considered worth returning if it is relevant to multiple research topics or aligns closely with the user's research interests.
    Use the score scale to assess how well the paper matches the research interests. Prioritize those with a score of 8 or higher.

    **Score Scale**
    Please use the following score scale:
    - 0: Completely irrelevant, no connection to the user's research interests.
    - 1: Marginal relevance, only a passing mention of a related topic or term.
    - 2: Very weak match, some relevant keywords but minimal applicability to user interests.
    - 3: Weak relevance, touches on similar areas but diverges in focus or application.
    - 4: Low relevance, shares a few broad themes with user research but lacks depth in key topics.
    - 5: Moderate relevance, overlaps with at least one research topic but lacks alignment with others.
    - 6: Fair relevance, aligns with at least one research topics, but not a precise fit.
    - 7: Good relevance, several overlapping topics. While some topics are peripheral, the paper is worth reading.
    - 8: Very high relevance, the paper strongly aligns with multiple research topics and matches user interests well.
    - 9: Excellent relevance, the paper is highly aligned with the user's research interests and offers valuable insights.
    - 10: Must read, this paper is directly applicable to the user's research and addresses core questions or problems in their field.

    Papers with a score of 7 or higher should be returned to the user.

    Paper Title: {paper_dict['title']}
    Paper Abstract: {paper_dict['abstract']}

    User's Research Topics:
    {", ".join(RESEARCH_TOPICS)}

    User's Research Interests:
    {USER_RESEARCH_INTERESTS}

    Response format (make sure it is parsable by JSON):
    {{
        "relevance_score": "",  # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10.
        "thoughts": "",  # Explain your reasoning for the assigned relevance score, thinking step-by-step.
        "summary": "",  # Summarize the paper's main contribution in 1-2 sentences.
        "relevant_topics": []  # List of the user's research topics that the paper is relevant to.
    }}
    """

async def evaluate_paper_relevance_async(paper_dict):
    prompt = create_prompt(paper_dict)
    return await OpenAIChat.chat(prompt)

async def process_batch(batch, delay_between_batches=3):
    results = []
    for paper_dict in batch:
        try:
            if is_preferred_paper(paper_dict):
                evaluation = {
                    "relevance_score": 10,
                    "thoughts": "Paper by preferred author or from preferred affiliation",
                    "summary": "See abstract for details.",
                    "relevant_topics": "Preferred paper."
                }
                results.append((paper_dict, evaluation))
            else:
                result = await evaluate_paper_relevance_async(paper_dict)
                results.append((paper_dict, result))
        except OpenAIError as e:
            print(f"Error processing paper: {e}")
            results.append((paper_dict, None))
    await asyncio.sleep(delay_between_batches)  # Wait between batches
    return results

async def filter_papers_by_relevance_async(fetched_papers, batch_size=5):
    tasks = []
    for i in range(0, len(fetched_papers), batch_size):
        batch = fetched_papers[i:i + batch_size]
        tasks.append(process_batch(batch))

    results = await asyncio.gather(*tasks)
    relevant_papers = [(paper, eval) for batch in results for paper, eval in batch if eval and int(eval['relevance_score']) >= 7]
    return relevant_papers

def get_relevant_papers(fetched_papers):
    relevant_papers = asyncio.run(filter_papers_by_relevance_async(fetched_papers))
    sorted_papers = sorted(
        relevant_papers, 
        key=lambda x: int(x[1]['relevance_score']),  # Convert to int
        reverse=True
    )
    return sorted_papers