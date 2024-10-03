from flask import Flask, render_template, request, redirect, url_for, flash, Response, stream_with_context
import datetime
import requests
import os
import json
import logging
from openai import OpenAI
from bs4 import BeautifulSoup  # Add this line
from tavily import TavilyClient
import time


app = Flask(__name__)
app.secret_key = 'kaan'  # Necessary for flashing messages

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for detailed logs
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()

# Retrieve API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
fmp_api_key = os.getenv("FMP_API_KEY")

# Directory where reports will be saved
REPORTS_DIR = 'saved_reports'
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_financial_data(symbol):
    base_url = "https://financialmodelingprep.com/api/v3"
    endpoints = {
        "income_statement": "income-statement",
        "balance_sheet": "balance-sheet-statement",
        "cash_flow": "cash-flow-statement",
        "profile": "profile",
        "ratios": "ratios"
    }
    data = {}
    for key, endpoint in endpoints.items():
        url = f"{base_url}/{endpoint}/{symbol}?apikey={fmp_api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data[key] = response.json()
            logging.info(f"Fetched {endpoint} for {symbol}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch {endpoint} for {symbol}: {e}")
            data[key] = []
    return data

def save_report(report_data, filename):
    filepath = os.path.join(REPORTS_DIR, f"{filename}.json")
    try:
        with open(filepath, 'w') as file:
            json.dump(report_data, file, indent=4)
        logging.info(f"Report saved successfully at: {filepath}")
    except Exception as e:
        logging.error(f"Failed to save report: {e}")

def get_saved_reports():
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(REPORTS_DIR, filename)
            try:
                with open(filepath, 'r') as file:
                    report_data = json.load(file)
                    reports.append({
                        "title": report_data.get('title_and_date', 'Untitled Report'),
                        "filename": filename.replace('.json', '')
                    })
            except Exception as e:
                logging.error(f"Failed to load the report {filename}: {e}")
    return reports

def load_report(filename):
    filepath = os.path.join(REPORTS_DIR, f"{filename}.json")
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"Report {filename} not found.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON for report {filename}.")
        return {}
    except Exception as e:
        logging.error(f"Failed to load the report {filename}: {e}")
        return {}
    
def perform_web_searches(company_name, symbol):
    # Define optimized search queries
    queries = [
        f"Latest news on {company_name} ({symbol})",
        f"Recent Federal Reserve announcements affecting {symbol}",
        f"Latest earnings report for {company_name} ({symbol}) and its impact on stock performance",
        f"Current macroeconomic factors influencing {company_name} ({symbol}) in short and long term"
    ]
    
    search_results = {}
    
    for query in queries:
        try:
            response = tavily_client.qna_search(query=query)
            search_results[query] = response
        except Exception as e:
            print(f"Failed to perform search for query '{query}': {e}")
            search_results[query] = "No data available."
            
    return search_results

    
def generate_daily_report(symbol):
    financial_data = get_financial_data(symbol)
    
    if not financial_data['profile']:
        return {
            "title_and_date": f"<h1>Error</h1><p>No profile data found for symbol {symbol}. Please check the symbol and try again.</p>",
            "company_profile": "",
            "financial_summary": "",
            "analysis": "",
            "action_recommendation": "",
            "short_term_outlook": "",
            "long_term_outlook": ""
        }
    
    income_statement = financial_data['income_statement'][0] if financial_data['income_statement'] else {}
    balance_sheet = financial_data['balance_sheet'][0] if financial_data['balance_sheet'] else {}
    cash_flow = financial_data['cash_flow'][0] if financial_data['cash_flow'] else {}
    profile = financial_data['profile'][0]
    ratios = financial_data['ratios'][0] if financial_data['ratios'] else {}
    
    current_date = datetime.date.today().strftime("%B %d, %Y")
    
    # Perform web searches using Tavily AI
    company_name = profile.get('companyName', symbol)
    search_results = perform_web_searches(company_name, symbol)
    
    # Construct the prompt with web search results
    prompt = f"""
    You are a highly experienced financial analyst tasked with generating a comprehensive daily research report on {company_name} ({symbol}). The report must empower decision-making by providing actionable insights based on financial data and recent news from web searches. Even if certain data is unavailable, provide a brief explanation or placeholder text.
    
    Incorporate the following web search results into the report for the latest developments:
    
    {json.dumps(search_results, indent=4)}

    **Formatting Guidelines**:
    - Use <h1> for the main title.
    - Use <h2> for each section title.
    - Use <p> for paragraphs.
    - Use <strong> for subtitles within sections.
    - Use <ul> and <li> for bullet points.
    
    **Data Provided**:
    
    <h1>Daily Research Report on {company_name} ({symbol})</h1>
    <p><strong>Date:</strong> {current_date}</p>
    
    <h2>Company Profile</h2>
    <ul>
        <li><strong>Market Capitalization:</strong> {profile.get('mktCap', 'N/A')}</li>
        <li><strong>Price to Earnings (P/E) Ratio:</strong> {ratios.get('priceEarningsRatio', 'N/A')}</li>
        <li><strong>Dividend Yield:</strong> {profile.get('lastDiv', 'N/A')}</li>
        <li><strong>Sector:</strong> {profile.get('sector', 'N/A')}</li>
        <li><strong>Industry:</strong> {profile.get('industry', 'N/A')}</li>
    </ul>
    
    <h2>Financial Summary</h2>
    <p><strong>Income Statement:</strong> Revenue: {income_statement.get('revenue', 'N/A')}, Net Income: {income_statement.get('netIncome', 'N/A')}</p>
    <p><strong>Balance Sheet:</strong> Total Assets: {balance_sheet.get('totalAssets', 'N/A')}, Total Liabilities: {balance_sheet.get('totalLiabilities', 'N/A')}</p>
    <p><strong>Cash Flow:</strong> Operating Cash Flow: {cash_flow.get('netCashProvidedByOperatingActivities', 'N/A')}, Free Cash Flow: {cash_flow.get('freeCashFlow', 'N/A')}</p>
    
    <h2>Analysis</h2>
    <p><strong>Revenue Growth:</strong> Analyze the revenue trends and their implications, based on historical data and future projections.</p>
    <p><strong>Profit Margins:</strong> Discuss gross, operating, and net profit margins, and assess the company's cost efficiency and operational effectiveness.</p>
    <p><strong>Financial Stability:</strong> Evaluate liquidity, solvency, and balance sheet health, considering the company's ability to meet short and long-term obligations.</p>
    <p><strong>Current News:</strong> Based on the provided web searches, summarize the latest news, including recent Fed announcements, company updates, and macroeconomic trends that could affect {symbol}'s performance.</p>
    
    <h2>Action Recommendation</h2>
    <p><strong>Recommendation:</strong> Provide a recommendation to either Buy, Sell, or Hold the stock, with a clear rationale based on the financial and news analysis.</p>
    
    <h2>Short-term Outlook</h2>
    <p>Provide a 3-6 month outlook, focusing on potential opportunities (e.g., new product launches, market expansion) and risks (e.g., economic downturns, regulatory changes) that could affect short-term performance. Include recent announcements and macroeconomic factors where relevant.</p>
    
    <h2>Long-term Outlook</h2>
    <p>Discuss the company's 1-4 year prospects, focusing on industry trends, the company’s strategy, and external macroeconomic factors (e.g., global economic recovery, technological advancements) that could impact {symbol} over the long-term.</p>
    """
    
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": prompt}
            ]
            
        )
        
        generated_content = completion.choices[0].message.content
        logging.info("OpenAI report generated successfully.")
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        generated_content = "<h2>Analysis</h2><p>Failed to generate analysis.</p>"
        
    # Initialize all sections to "Content not available"
    report_sections = {
        "title_and_date": "",
        "company_profile": "",
        "financial_summary": "",
        "analysis": "",
        "action_recommendation": "",
        "short_term_outlook": "",
        "long_term_outlook": ""
    }
    
    # Parse the generated_content
    soup = BeautifulSoup(generated_content, 'html.parser')
    
    # Extract Title and Date (h1)
    h1 = soup.find('h1')
    if h1:
        p_date = h1.find_next_sibling('p')
        title_and_date = f"{str(h1)} {str(p_date) if p_date else ''}"
        report_sections['title_and_date'] = title_and_date
    else:
        report_sections['title_and_date'] = "<h1>Title Not Available</h1>"
        
    # Extract all h2 sections
    for h2 in soup.find_all('h2'):
        section_title = h2.get_text(strip=True).lower().replace(' ', '_')
        # Normalize section titles to match keys
        normalized_title = section_title.replace('-', '_').replace('/', '_')
        if normalized_title in report_sections:
            # Get all content until the next h2
            content = []
            for sibling in h2.next_siblings:
                if sibling.name == 'h2':
                    break
                if isinstance(sibling, str):
                    continue
                content.append(str(sibling))
            section_content = ''.join(content).strip()
            if section_content:
                report_sections[normalized_title] = f"<h2>{h2.get_text(strip=True)}</h2>{section_content}"
            else:
                # If no content, provide a default message
                report_sections[normalized_title] = f"<h2>{h2.get_text(strip=True)}</h2><p>Content not available.</p>"
                
    # Ensure all required sections are present
    required_sections = ["title_and_date", "company_profile", "financial_summary",
                         "analysis", "action_recommendation", "short_term_outlook", "long_term_outlook"]
    for sec in required_sections:
        if not report_sections.get(sec):
            report_sections[sec] = f"<h2>{sec.replace('_', ' ').title()}</h2><p>Content not available.</p>"
            
    # Log the sections to verify
    for key, value in report_sections.items():
        logging.info(f"Section [{key}]: {'Available' if value else 'Missing'}")
        
    return report_sections



# ============================
# 5. Define Flask Routes
# ============================

@app.route('/')
def index():
    # Get the symbol from query parameters; default to 'NVDA' if not provided
    symbol = request.args.get('symbol', default='NVDA', type=str).upper()
    logging.info(f"Index page accessed with symbol: {symbol}")
    return render_template('index.html', symbol=symbol)

@app.route('/daily-report', methods=['GET', 'POST'])
def daily_report():
    if request.method == 'POST':
        if 'save_report' in request.form:
            # Handle saving the report
            report_json = request.form.get('report-data')
            symbol = request.form.get('symbol')
            logging.debug(f"Received symbol: {symbol}")
            logging.debug(f"Received report-data: {report_json}")
            
            if not report_json or not symbol:
                flash("Invalid data for saving the report.", "error")
                return redirect(url_for('daily_report'))
            
            try:
                report = json.loads(report_json)
                filename = f"{symbol}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                save_report(report, filename)
                logging.info(f"Report saved as: {filename}.json")
                flash("Report saved successfully!", "success")
                return redirect(url_for('saved_reports'))
            except json.JSONDecodeError as e:
                logging.error(f"JSONDecodeError: {e}")
                flash("Failed to decode report data.", "error")
                return redirect(url_for('daily_report'))
        else:
            symbol = request.form.get('stock-symbol').strip().upper()
            logging.info(f"Form submitted with symbol: {symbol}")
            
            if not symbol:
                flash("Please enter a stock symbol.", "error")
                return redirect(url_for('daily_report'))
            
            # Stream response while generating the report
            def stream_report():
                for _ in range(5):  # Send heartbeat bytes every 5 seconds
                    yield " "  # Send a single byte (space) to keep the connection alive
                    time.sleep(5)  # Simulate long process
                
            # Generate the report first, then render the template once ready
            report = generate_daily_report(symbol)  # Your long-running function
            logging.info(f"Report generated for symbol: {symbol}")
            
            # Return the streamed content + the final rendered template
            return render_template('daily_report.html')
        
    else:
        # GET request
        return render_template('daily_report.html')
    

@app.route('/saved-reports')
def saved_reports():
    reports = get_saved_reports()
    return render_template('saved_reports.html', reports=reports)

# Flask route to view a saved report
@app.route('/view-report/<filename>')
def view_report(filename):
    report = load_report(filename)
    return render_template('view_report.html', report=report)

@app.route('/delete-report/<filename>', methods=['POST'])
def delete_report(filename):
    # Security Check: Ensure filename is safe
    if '..' in filename or filename.startswith('/'):
        flash("Invalid report filename.", "error")
        return redirect(url_for('saved_reports'))
    
    filepath = os.path.join(REPORTS_DIR, f"{filename}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logging.info(f"Report deleted successfully: {filepath}")
            flash("Report deleted successfully.", "success")
        except Exception as e:
            logging.error(f"Failed to delete report {filepath}: {e}")
            flash("Failed to delete the report.", "error")
    else:
        logging.warning(f"Attempted to delete non-existent report: {filepath}")
        flash("Report not found.", "error")
        
    return redirect(url_for('saved_reports'))

if __name__ == '__main__':
    app.run(debug=True)
    
    
    