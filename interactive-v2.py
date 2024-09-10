## Screening functionality alone
# Primary search with spacy

import streamlit as st
import pandas as pd
from groq import Groq
import spacy
from nltk.stem.snowball import SnowballStemmer

nlp = spacy.load('en_core_web_sm')

stemmer = SnowballStemmer("english")

client = Groq(api_key= st.secrets["groq_passkey"])



st.title("Interactive Selection")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "df" not in st.session_state:
    st.session_state.df = None

if "keyword" not in st.session_state:
    st.session_state.keyword = None

user_prompt = None

uploaded_file = st.file_uploader("Choose a file with candidate information. Acceptable formates are excel and csv:",type =["csv","xlsx","xls"])

def file_reader(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

abbreviations={
    "ml" : "machine learning",
    "ai" : "artificial intelligence",
    "nlp" : "natural language processing",
    "eda" : "exploratory data analysis",
    "aiml" : "AI/ML"
}

def nlp_search(text, word):
    for token in nlp(text):
        if stemmer.stem(abbreviations.get(token.text.lower(),token.text.lower())) == stemmer.stem(word):
            return True
        elif stemmer.stem(abbreviations.get(token.text.lower(),token.text.lower())) == stemmer.stem(abbreviations.get(word,word)):
            return True
    return False

def my_search(keyword):
    if "Skill" in st.session_state.df.columns:
        return st.session_state.df[st.session_state.df["Skill"].map(lambda x : nlp_search(x,word =keyword) if pd.notnull(x) else False)]
        
    elif "Skills" in st.session_state.df.columns:
        return st.session_state.df[st.session_state.df["Skills"].map(lambda x : nlp_search(x,word =keyword) if pd.notnull(x) else False)]
    
    else:
        st.error("The given file does not contain a skill column.")



if uploaded_file:
    st.write("File preview")
    try:    
        st.session_state.df = file_reader(uploaded_file)
    except Exception as ex:
        st.error("Failed to read file due to the following reasons:",ex)
    st.dataframe(st.session_state.df.head())
    st.write("There are {} total candidates.".format(len(st.session_state.df)))

if st.session_state.df is not None:
    st.header("Candidate Screening")
    st.session_state.keyword = st.text_input("Enter the primary skill for screening (eg: python, sql, etc.)")
    st.session_state.mydf = my_search(st.session_state.keyword)
    

if st.session_state.keyword:
    st.write("Candidate list filtered succesfully")
    st.write("There are {} total candidates, having {} skillset.".format(len(st.session_state.mydf),st.session_state.keyword))
    st.dataframe(st.session_state.mydf)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Enquire about the candidates")



if user_prompt:
    st.chat_message("user").markdown(user_prompt)  
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})  

    full_prompt = f"""
    You are an advanced data analysis model designed to provide precise and consistent answers based on the given DataFrame {st.session_state.mydf.to_string()}

    Question to respond: {user_prompt}

    If retreval of records is required, present the records with all relevant details in a tabular format.
    
    """
    chat = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": full_prompt,
            }
        ],
        model="llama3-8b-8192",
        temperature = 0.5
    )

    assistant_response = chat.choices[0].message.content  
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})  

    with st.chat_message("assistant"):
        st.markdown(assistant_response)


