import os
import pandas as pd
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
import http.client
import json
import requests

# Load supplier and client lists from Excel
excel_path = r'C:\\Users\\Merlin\\Downloads\\BBA COURSEWORK\\PROJECTS\\DATATHON\\Suppliers and client list .xlsx'
suppliers_df = pd.read_excel(excel_path, sheet_name=0)
clients_df = pd.read_excel(excel_path, sheet_name=1)

# Format suppliers list for prompt
supplier_list = "\n".join(
    f"{row['Supplier Name']}\t{row['Product Supplied']}\t{row['Location']}\t{row['Product Turned Into']}" 
    for index, row in suppliers_df.iterrows()
)

# Format clients list for alerts in BCP
client_list = "\n".join(
    f"{row['Client Name']}\t{row['Location']}\t{row['Product Ordered by clients']}" 
    for index, row in clients_df.iterrows()
)

# Configure environment and load news
os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0"
url = "https://safety4sea.com/xeneta-impending-port-strikes-threaten-u-s-supply-chains-and-economic-stability/"

# News scraping
article_source = "reuters" if "reuters.com" in url else "other"
if article_source.lower() == "other":
    loader = AsyncChromiumLoader([url])
    tt = Html2TextTransformer()
    docs = tt.transform_documents(loader.load())
    news_content = docs[0].page_content
else:
    # Reuters API
    conn = http.client.HTTPSConnection("reuters-scraper.p.rapidapi.com")
    payload = json.dumps([{"url": url}])
    headers = {
        'x-rapidapi-key': "********",#Key masked 
        'x-rapidapi-host': "reuters-scraper.p.rapidapi.com",
        'Content-Type': "application/json"
    }
    conn.request("POST", "/api/news/reuters-scraper/news", payload, headers)
    res = conn.getresponse()
    data = res.read()
    decoded_data = data.decode("utf-8")
    articles = json.loads(decoded_data)
    news_content = articles[0].get("content", "No content found") if articles else "No content found"

# OpenAI API configuration
api_key = '************'#Key masked due to security reason
url = "https://api.openai.com/v1/chat/completions"
headers = {
     "Content-Type": "application/json",
     "Authorization": f"Bearer {api_key}"
}

# Prompt for news extraction, classification, and supplier-client analysis
consolidated_prompt = {
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant lookingover the supplychain for Silicon Valley semiconductor and electronics manufacturer based in USA which serves various industries, including consumer electronics, defense, and renewable energy. It specializes in high-performance computing and IoT solutions, offering energy-efficient products like semiconductor chips and custom components."},
        {
            "role": "user",
            "content": (
                f"Extract and summarize the main content with all the relevant facts from the provided news article, omitting advertisements, author details, and other non-news elements in 150 words. "
                f"Then classify the article as Trade, Geopolitical, Transportation, Natural Disaster, or Other." 
                f"Example for Trade article:Chinese smartphone brand Honor is set to relaunch in India through a licensing deal with a local company, aiming to start domestic manufacturing by early next year. Honor had previously retreated from the Indian market due to limited marketing budget and portfolio management issues. The comeback is facilitated by a deal with Gurugram-based Honor Tech, which will manufacture, sell, and service Honor-branded smartphones in India. The company plans to launch three phone variants, with the mid-range Number series expected by September. Honor Tech aims to capture a 5% market share in India by 2024, targeting a revenue of at least 100 billion rupees ($1.20 billion)."
                f"Example for Geopolitical article:China and Russia have criticized Japan for its decision to discharge radioactive water from the Fukushima nuclear plant into the sea, arguing it is based on economic rather than scientific reasons. They suggest that evaporating the water would be safer, though more costly. Despite protests, Japan plans to proceed with the discharge, which the International Atomic Energy Agency has approved, stating it meets international standards and will have a negligible impact. "
                f"Example for Transportation article:U.S. workers at UPS have ratified a new five-year contract, averting a potential strike that could have disrupted Christmas deliveries and increased shipping costs. The agreement raises pay, eliminates a two-tier wage system, and adds benefits like another paid holiday and air conditioning in new trucks. The contract, ratified by 86.3% of voting members, provides significant wage increases for part-time workers and addresses key issues like seniority-based wage tiers. UPS, the largest package delivery company, handles about a quarter of U.S. parcel deliveries. The deal is seen as a win for unions and a potential model for other companies. UPS had previously cut its revenue and profitability targets due to higher labor costs and business lost during contract talks."
                f"Example for natural disaster article:A magnitude 5.1 earthquake occurred in the United States near Santa Barbara, CA on 20 Aug 2023, with a depth of 4.8 km. It affected around 20,000 people, classed as having a low humanitarian impact."
                f"Else it should be categorised as other when the article is irrelevant to our company, suppliers or clients"
                f"After classification, analyze the potential impact of the news on the company's supply chain based on the provided supplier and client lists, identifying ALL clients THAT should be alerted by us for not able to deliver the products ordered due to location of the event ,inventory, logistics/deliveries or other reasons etc. Identify all our suppliers who won't be able to satify our requirements due to the direct impact of the event on them"
                f"Note that the suppliers are not related to each other.\n\n"
                f"Content: {news_content}\n\n"
                f"List of suppliers:\n{supplier_list}\n\n"
                f"List of clients:\n{client_list}\n\n"
                f"**Risk Score Calculation**:\n"
                f"1. **Severity (S)**: 1 = Minimal impact on production, 2 = Low impact; slight delays in non-critical areas, 3 = Moderate impact; some key processes affected, 4 = High impact; significant delays or disruptions, 5 = Very severe; major production halt or facility shutdown.\n"
                f"2. **Proximity (P)**: 1 = Very far (no direct impact),2 = Some distance (minor impact),3 = Moderate distance (noticeable effect),4 = Close proximity (could affect operations),5 = Directly affects local operations (e.g., nearby factory)\n"
                f"3. **Duration (D)**: 1 = Short-term (hours to days),2 = Temporary (weeks),3 = Medium-term (1-3 months),4 = Long-term (3-6 months),5 = Extended (more than 6 months)\n"
                f"4. **Impact on Key Suppliers (I)**: 1 = No impact on suppliers,2 = Minor impact on non-critical suppliers,3 = Moderate impact on some key suppliers,4 = Significant impact on multiple key suppliers,5 = Critical impact on essential suppliers (e.g., shortages of silicon wafers)\n"
                f"5. **Weights**: Weight for Severity (W_s): 2.5 (high importance due to production impact),Weight for Proximity (W_p): 1.5 (moderate importance; local events can be critical),Weight for Duration (W_d): 1.0 (important but less critical than severity),Weight for Impact on Key Suppliers (W_i): 2.0 (essential for assessing supplier reliability)\n"
                f"6. **Formula**:\n"
                f"   Risk Score=((S×2.5)+(P×1.5)+(D×1.0)+(I×2.0)/50)*10\n"
                f"   - 0-2: Low Risk (minimal impact)\n"
                f"   - 2-5: Moderate Risk (some disruptions)\n"
                f"   - 5-8: High Risk (significant disruptions)\n"
                f"   - 8-10: Critical Risk (severe impact)\n\n"
                f"Provide the output in only the following JSON format :\n"
                f"{{ \"summary\": \"<summary of article>\", \"classification\": \"<Trade/Geopolitical/Transportation/Natural Disaster/Other>\", "
                f"\"suppliers_affected\": [{{\"supplier_name\": \"<supplier 1>\", \"reason\": \"<reason for impact>\", \"profile\": \"<supplier profile>\"}}, "
                f"{{\"supplier_name\": \"<supplier 2>\", \"reason\": \"<reason for impact>\", \"profile\": \"<supplier profile>\"}}, ...], "
                f"\"clients_to_be_alerted\": {{\"client1\": \"reason\", \"client2\": \"reason\", \"client_n\": \"reason\"}}, "
                f"\"risk_score_of_the_event\": \"<Risk Score>/10\" }}"
            )
        }
    ],"temperature": 0.1
}

response = requests.post(url, headers=headers, data=json.dumps(consolidated_prompt))
response_data = response.json()
supplier_client_output = response_data['choices'][0]['message']['content'] if 'choices' in response_data else "No supplier-client response"

print("Supplier and Client Output:", supplier_client_output)

