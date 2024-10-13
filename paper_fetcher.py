import arxiv
from datetime import datetime, timedelta
import pickle
from pymed import PubMed
from user_preferences import RESEARCH_TOPICS, PREFERRED_AUTHORS, PUBMED_JOURNALS
import time

SOURCES = [
    "biorxiv",
    "arxiv",
    "medrxiv",
    "pubmed"
]
MAX_RESULTS = 5
PAST_DAYS = 3

def collect_papers(is_save=False):
    fetched_papers = []
    
    today = datetime.now().date()
    start_date = today - timedelta(days=PAST_DAYS)

    for source in SOURCES:
        print(f"Fetching papers from {source} starting on {start_date}...")
        source_papers = fetch_papers(source, start_date, RESEARCH_TOPICS, PREFERRED_AUTHORS, PUBMED_JOURNALS)
        fetched_papers.extend(source_papers)
        print(f"Found {len(source_papers)} papers from {source}")

    if is_save:
        with open(f'papers_{start_date}_{PAST_DAYS}d.pkl', 'wb') as f:
            pickle.dump(fetched_papers, f)

    print(f"Total papers found: {len(fetched_papers)}")
    return fetched_papers

def fetch_papers(source, start_date, topics, authors, PM_journals):
    if source.lower() == "arxiv":
        return fetch_arxiv_papers(start_date, topics, authors)
    elif source.lower() == "biorxiv":
        return fetch_biorxiv_papers(start_date, topics, authors)
    elif source.lower() == "medrxiv":
        return fetch_medrxiv_papers(start_date, topics, authors)
    elif source.lower() == "pubmed":
        return fetch_pubmed_papers(start_date, topics, authors, PM_journals)
    else:
        print(f"Unknown source: {source}")
        return []

def fetch_arxiv_papers(start_date, topics, authors):
    query = " OR ".join([f"abs:{topic}" for topic in topics])
    query += " OR ".join([f"au:{author}" for author in authors])

    client = arxiv.Client()
    search = arxiv.Search(
        query = query,
        max_results = MAX_RESULTS,
        sort_by = arxiv.SortCriterion.SubmittedDate
    )
    results = client.results(search)

    papers = []
    for result in client.results(search):
        if result.published.date() >= start_date:
            paper = {
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'published': result.published.date(),
                'pdf_url': result.pdf_url,
                'abstract': result.summary,
                'journal': "arXiv",
                'affiliations': ""
            }
            papers.append(paper)
        else:
            break
    return papers

def fetch_pubmed_papers(start_date, topics, authors, PM_journals):
    pubmed = PubMed()
    
    topic_query = " OR ".join([f'"{topic}"[Title/Abstract]' for topic in topics])
    author_query = " OR ".join([f'"{author}"[Author]' for author in authors])
    combined_query = f"({topic_query}) OR ({author_query})"

    journal_query = " OR ".join([f'"{journal}"[Journal]' for journal in PM_journals])
    combined_query = f"{combined_query} AND ({journal_query})"
    
    date_range = f"({start_date.strftime('%Y/%m/%d')}[epdat] : 3000[epdat])"
    additional = '("Journal Article"[Publication Type])'
    query = f"{combined_query} AND {date_range} AND {additional}"

    max_attempts = 5
    attempt = 0
    papers = []

    while attempt < max_attempts:
        try:
            response = pubmed.query(query, max_results=MAX_RESULTS)
            
            for article in response:
                author_names = [
                    f"{(author['firstname'] or '').strip()} {(author['lastname'] or '').strip()}".strip()
                    for author in article.authors
                ]
                author_names = [name for name in author_names if name is not None and name != '']
                affiliations = list(set([author['affiliation'] for author in article.authors if author['affiliation'] is not None and author['affiliation'] != '']))
                
                paper = {
                    'title': article.title,
                    'authors': author_names,
                    'published': article.publication_date,
                    'pdf_url': f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id.split('\n')[0]}/",
                    'abstract': article.abstract,
                    'journal': article.journal,
                    'affiliations': affiliations
                }
                papers.append(paper)
            break
        except Exception as e:
            attempt += 1
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_attempts:
                time.sleep(1)  # Sleep for 1 second before retrying
            else:
                print("Max attempts reached. Unable to fetch papers from PubMed.")
                return []

    return papers

def fetch_biorxiv_papers(start_date, topics, authors):
    # Implement bioRxiv paper fetching
    return []

def fetch_medrxiv_papers(start_date, topics, authors):
    # Implement medRxiv paper fetching
    return []
