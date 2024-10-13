from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
import json
import re
from datetime import date
from user_preferences import RESEARCH_TOPICS, PREFERRED_AUTHORS, PREFERRED_AFFILIATIONS, USER_RESEARCH_INTERESTS

class OpenAIChat:
    model = ChatOpenAI(
        openai_api_key=open('.openai_api_key').read().strip(),
        model_name='gpt-4o'
    )

    @classmethod
    def chat(cls, request):
        response = cls.model.invoke([HumanMessage(content=request)]).content
        
        # Strip any extraneous formatting characters
        response = response.strip().strip('```json').strip('```')
        
        # Escape invalid characters for JSON
        response = re.sub(r'\\', r'\\\\', response)  # Escape backslashes
        response = re.sub(r'\$', '', response)  # Remove dollar signs used in LaTeX

        try:
            json_response = json.loads(response)
        except json.JSONDecodeError:
            # Retry with a reminder for JSON format
            reminder_request = request + "\n\nPlease ensure the response is in valid JSON format."
            response = cls.model.invoke([HumanMessage(content=reminder_request)]).content
            response = response.strip().strip('```json').strip('```')
            response = re.sub(r'\\', r'\\\\', response)
            response = re.sub(r'\$', '', response)

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

def is_preferred_paper(paper_dict):
    return (any(author in PREFERRED_AUTHORS for author in paper_dict['authors']) or
            any(affiliation in PREFERRED_AFFILIATIONS for affiliation in paper_dict['affiliations']))

def evaluate_paper_relevance(paper_dict):
    prompt = f"""
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
    - 9: Excellent relevance, the paper is highly aligned with the user’s research interests and offers valuable insights.
    - 10: Must read, this paper is directly applicable to the user’s research and addresses core questions or problems in their field.

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
    return OpenAIChat.chat(prompt)

def filter_papers_by_relevance(fetched_papers):
    relevant_papers = []
    for paper_dict in fetched_papers:
        if is_preferred_paper(paper_dict):
            evaluation = {
                "relevance_score": 10,
                "thoughts": "Paper by preferred author or from preferred affiliation",
                "summary": "See abstract for details.",
                "relevant_topics": "Preferred paper."
            }
        else:
            evaluation = evaluate_paper_relevance(paper_dict)
        
        if int(evaluation['relevance_score']) >= 7:
            relevant_papers.append((paper_dict, evaluation))
    return relevant_papers

def get_relevant_papers(fetched_papers):
    relevant_papers = filter_papers_by_relevance(fetched_papers)
    sorted_papers = sorted(relevant_papers, key=lambda x: x[1]['relevance_score'], reverse=True)
    print(sorted_papers)
    return sorted_papers
