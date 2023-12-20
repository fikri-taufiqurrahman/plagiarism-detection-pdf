import streamlit as st
import os
# import nltk 
# nltk.download('punkt')

from PyPDF2 import PdfReader
import pandas as pd
from nltk import tokenize
from bs4 import BeautifulSoup
import requests
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        # Buat objek PDFReader
        pdf_reader = PdfReader(file)

        # Inisialisasi string untuk menyimpan teks dari semua halaman
        text = ""

        # Iterasi melalui halaman-halaman PDF
        for page_number in range(len(pdf_reader.pages)):
            # Dapatkan objek halaman
            page = pdf_reader.pages[page_number]

            # Ekstrak teks dari halaman
            text += page.extract_text()

        return text
    
def get_sentences(text):
    sentences = tokenize.sent_tokenize(text)
    return sentences

def get_url(sentence):
    base_url = 'https://www.google.com/search?q='
    query = sentence
    query = query.replace(' ', '+')
    url = base_url + query
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    divs = soup.find_all('div', class_='yuRUbf')
    urls = []
    for div in divs:
        a = div.find('a')
        urls.append(a['href'])
    if len(urls) == 0:
        return None
    elif "youtube" in urls[0]:
        return None
    else:
        return urls[0]
    

    
def get_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = ' '.join(map(lambda p: p.text, soup.find_all('p')))
    return text

def get_similarity(text1, text2):
    text_list = [text1, text2]
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(text_list)
    similarity = cosine_similarity(count_matrix)[0][1]
    return similarity

def get_similarity_list(text, url_list):
    similarity_list = []
    for url in url_list:
        text2 = get_text(url)
        similarity = get_similarity(text, text2)
        similarity_list.append(similarity)
    return similarity_list

st.set_page_config(page_title='Plagiarism Detection')
st.title('Plagiarism Detection')

st.write("""
### Enter the text to check for plagiarism
""")

# Widget untuk mengunggah file
uploaded_file = st.file_uploader("Pilih file (pdf)", type=["pdf"])
# Jika file diunggah
# Jika file diunggah
if uploaded_file is not None:
    # Simpan file di direktori yang sama dengan skrip
    file_path = os.path.join(os.getcwd(), uploaded_file.name)
    
    with open(file_path, "wb") as file:
        file.write(uploaded_file.read())

    st.success(f"File '{uploaded_file.name}' berhasil diunggah dan disimpan di {file_path}")
    
pdf_path = 'Abstract.pdf'
text = extract_text_from_pdf(pdf_path)

# text = st.text_area("Enter text here", height=200)

url = []

if st.button('Check for plagiarism'):
    st.write("""
    ### Checking for plagiarism...
    """)
    sentences = get_sentences(text)
    for sentence in sentences:
        url.append(get_url(sentence))
    if None in url:
        st.write("""
        ### No plagiarism detected!
        """)
        st.stop()
    similarity_list = get_similarity_list(text, url)
    df = pd.DataFrame({'Sentence': sentences, 'URL': url, 'Similarity': similarity_list})
    df = df.sort_values(by=['Similarity'], ascending=False)
    df = df.reset_index(drop=True)
    st.table(df)


os.remove(file_path)
