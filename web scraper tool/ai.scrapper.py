# Import the required libraries
import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import pandas as pd
import io
from datetime import datetime
import socket
import time
import re
from scrapegraphai.graphs import SmartScraperGraph

# Set up the Streamlit app
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using BeautifulSoup and analyze it with Groq API")

# Get Groq API key from user
groq_api_key = st.text_input("Groq API Key", type="password")

if groq_api_key:
    # Set the environment variable for Groq
    os.environ["GROQ_API_KEY"] = groq_api_key
    
    model = st.radio(
        "Select the model",
        ["llama-3.3-70b-versatile", "llama-3.3-70b-instruct"],
        index=0,
    )
    
    # Get the URL of the website to scrape
    url = st.text_input("Enter the URL of the website you want to scrape")
    # Get the user prompt
    user_prompt = st.text_input("What you want the AI agent to analyze from the website?")
    
    if st.button("Scrape and Analyze"):
        try:
            # Add http:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Configure requests with retries and timeout
            session = requests.Session()
            session.verify = True  # Enable SSL verification
            
            # Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Try to resolve the domain first
            try:
                domain = url.split('//')[1].split('/')[0]
                socket.gethostbyname(domain)
            except socket.gaierror:
                st.error(f"Could not resolve the domain: {domain}")
                st.info("Please check if the website URL is correct and try again.")
                st.stop()
            
            # Make the request with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = session.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)  # Wait before retrying
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Initialize Groq client
            client = Groq(api_key=groq_api_key)
            
            # Prepare the prompt for analysis
            analysis_prompt = f"""
            Here is the content from the website {url}:
            
            {text_content[:4000]}  # Limiting content length
            
            Based on this content, {user_prompt}
            """
            
            # Get analysis from Groq
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                model=model,
                temperature=0.1,
            )
            
            # Get the analysis result
            analysis_result = chat_completion.choices[0].message.content
            
            # Display the results
            st.subheader("Analysis Results")
            st.write(analysis_result)
            
            # Clean up the analysis result for CSV
            cleaned_result = re.sub(r'```.*?```', '', analysis_result, flags=re.DOTALL)  # Remove code blocks
            cleaned_result = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', cleaned_result)  # Remove URLs
            cleaned_result = re.sub(r'\s+', ' ', cleaned_result).strip()  # Remove extra whitespace
            
            # Create a DataFrame with the analysis results
            df = pd.DataFrame({
                'Website URL': [url],
                'Analysis Prompt': [user_prompt],
                'Analysis Result': [cleaned_result],
                'Analysis Date': [datetime.now().strftime("%Y-%m-%d")],
                'Analysis Time': [datetime.now().strftime("%H:%M:%S")]
            })
            
            # Convert DataFrame to CSV
            csv = df.to_csv(index=False)
            
            # Create a download button for the CSV file
            st.download_button(
                label="Download Analysis as CSV",
                data=csv,
                file_name=f"web_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching the webpage: {str(e)}")
            st.info("Please try the following:")
            st.info("1. Check if the website URL is correct")
            st.info("2. Make sure you have a stable internet connection")
            st.info("3. Try again in a few moments")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Please try again or contact support if the issue persists")