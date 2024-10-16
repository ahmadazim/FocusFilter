from paper_fetcher import collect_papers
from llm import get_relevant_papers

def print_format(paper_obj, evaluation):
    authors_str = ",\n".join(paper_obj['authors'])
    affiliations_str = "\n".join(f"- {aff}" for aff in paper_obj['affiliations'])
    relevant_topics_str = ", ".join(evaluation['relevant_topics'])

    output = f"""📰  **Title:**  
{paper_obj['title']}

👥  **Authors:**  
{authors_str}

🏢  **Affiliations:**  
{affiliations_str}

📖  **Journal:** {paper_obj['journal']}  
📅  **Published:** {paper_obj['published']}  
🔗  **URL:** {paper_obj['pdf_url']}

📝  **Abstract:**  
{paper_obj['abstract']}

⭐  **Relevance Score:** {evaluation['relevance_score']}  
🧬  **Relevant Topics:** {relevant_topics_str}

🧐  **Explanation:**  
{evaluation['thoughts']}
"""
    return output

def main():
    IS_SAVE = True

    fetched_papers = collect_papers(is_save=IS_SAVE)
    print(f"Initially fetched {len(fetched_papers)} papers")

    relevant_papers = get_relevant_papers(fetched_papers)
    print(f"Found {len(relevant_papers)} relevant papers")

    for paper, evaluation in relevant_papers:
        print(print_format(paper, evaluation))
        print("=" * 50, "\n")

if __name__ == "__main__":
    main()
