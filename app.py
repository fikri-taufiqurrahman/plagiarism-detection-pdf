import base64
import streamlit as st
import pandas as pd
from nltk import tokenize
from bs4 import BeautifulSoup
import requests
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO
file_path =""

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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}
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

def extract_text_from_pdf(uploaded_file):
    with open(uploaded_file.name, "wb") as pdf_file:
        pdf_file.write(uploaded_file.getbuffer())
    doc = fitz.open(pdf_file.name)
    text = ''
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text += page.get_text()
    doc.close()
    return text

def create_pdf(results_df, pdf_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    data = [results_df.columns.tolist()] + results_df.values.tolist()
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    style.add('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    style.add('GRID', (0, 1), (-1, -1), 1, colors.black)
    style.add('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    style.add('BOTTOMPADDING', (0, 0), (-1, 0), 18)
    table.setStyle(style)
    doc.build([table])

def get_binary_file_downloader_html(buffer, file_name):
    with open(file_name, 'wb') as f:
        f.write(buffer.getbuffer())
    href = f'<a href="data:application/octet-stream;base64,{base64.b64encode(buffer.getvalue()).decode()}" download="{file_name}">Download Results PDF</a>'
    return href

st.set_page_config(page_title='Plagiarism Detection')
st.title('Plagiarism Detection')

st.write("""
### Enter the text to check for plagiarism
""")
uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])

url = []
if st.button('Check for plagiarism'):
    st.write(""
    ### Checking for plagiarism...
    "")
    if uploaded_file is not None:
        text = extract_text_from_pdf(uploaded_file)
    sentences = get_sentences(text)
    url = [get_url(sentence) for sentence in sentences]
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

if file_path:
    # Simpan hasil deteksi ke file PDF
    buffer = BytesIO()
    create_pdf(df, buffer)
    st.markdown(get_binary_file_downloader_html(buffer, "plagiarism_detection_results.pdf"), unsafe_allow_html=True)
    os.remove(file_path)
