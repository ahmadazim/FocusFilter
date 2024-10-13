# Paper Recommendation and Filtering

## Overview

This project is a paper filtering/recommendation system designed to help researchers pick the most relevant papers to read from the plethora of academic papers published daily on platforms like arXiv, bioRxiv, medRxiv, and PubMed. User interests, relevant research topics, important authors, and important author affiliations can be specified as filters to give personalized paper recommendations. Final paper recommendations are powered by LLMs.


## Usage

To use the paper recommendation system, follow these steps:

1. **Configure API Key**: Store your OpenAI API key in a file named `.openai_api_key`.
2. **Set Preferences**: Modify the variables in `user_preferences.py` to specify your research interests, important authors, important author affiliations, relevant research topics, and preferred PubMed journals.
3. **Specify Fetching Parameters**: Modify the variables in `paper_fetcher.py` to specify the number of days to fetch papers for (default is 3 days) and the maximum number of results to fetch (default is 100 papers from each source).
4. **Run the System**: Execute the main script to start filtering and receiving recommendations:
   ```bash
   python main.py
   ```

## Details

- The system first fetches papers from PubMed, bioRxiv, and medRxiv based on the user's research interests, important authors, and important author affiliations.
- Next, the system uses LLMs to evaluate the relevance of each paper to the user's research topics.
- Finally, the system returns the top-ranked papers to the user.
- Papers which are authored by the user's preferred authors or at the user's preferred affiliations are automatically included in the final results.


## Acknowledgement

This project was inspired by the [Arxiv-Recommender](https://github.com/Kaffaljidhmah2/Arxiv-Recommender/) repository!

