import streamlit as st
import duckdb
import pandas as pd
import time
import os

# 1. 데이터베이스 연결 (madang.db 파일 사용)
conn = duckdb.connect(database='madang.db', read_only=False)

# 2. 테이블이 없으면 CSV에서 로드 (배포 환경 호환성 확보)
try:
    conn.sql("CREATE TABLE IF NOT EXISTS Customer AS SELECT * FROM 'Customer_madang.csv'")
    conn.sql("CREATE TABLE IF NOT EXISTS Book AS SELECT * FROM 'Book_madang.csv'")
    conn.sql("CREATE TABLE IF NOT EXISTS Orders AS SELECT * FROM 'Orders_madang.csv'")
except Exception as e:
    st.error(f"데이터 로드 중 오류: {e}")

# 3. 쿼리 실행 함수
def query(sql):
    return conn.sql(sql).df()

# 4. 화면 구성 (UI)
st.title("마당서점 관리자 페이지")

# 도서 목록 가져오기
try:
    books_df = query("select bookid, bookname from Book")
    books_list = []
    for index, row in books_df.iterrows():
        books_list.append(f"{row['bookid']},{row['bookname']}")
except Exception:
    books_list = []

tab1, tab2 = st.tabs(["고객조회", "거래 입력"])

# [탭 1] 고객 조회
with tab1:
    st.header("고객 정보 조회")
    name_input = st.text_input("고객명 검색")
    
    if name_input:
        sql = f"""
            SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice 
            FROM Customer c, Book b, Orders o 
            WHERE c.custid = o.custid AND o.bookid = b.bookid AND c.name = '{name_input}'
        """
        result_df = query(sql)
        if not result_df.empty:
            st.dataframe(result_df)
            st.session_state['searched_custid'] = result_df.iloc[0]['custid']
            st.session_state['searched_name'] = result_df.iloc[0]['name']
        else:
            st.write("주문 내역이 없습니다.")

# [탭 2] 거래 입력
with tab2:
    st.header("새로운 거래 입력")
    custid = st.session_state.get('searched_custid', 0)
    custname = st.session_state.get('searched_name', "")
    
    st.write(f"고객번호: {custid} / 고객명: {custname}")
    select_book = st.selectbox("구매 서적 선택:", books_list)
    
    if st.button("주문 입력"):
        if custid == 0:
            st.warning("고객조회 탭에서 먼저 검색해주세요.")
        elif select_book:
            bookid = select_book.split(",")[0]
            # 가격 조회
            price_df = query(f"SELECT price FROM Book WHERE bookid = {bookid}")
            saleprice = price_df.iloc[0]['price'] if not price_df.empty else 0
            today = time.strftime('%Y-%m-%d')
            
            # 주문번호 생성 및 입력
            max_id = query("SELECT MAX(orderid) as m FROM Orders").iloc[0]['m']
            new_id = max_id + 1
            
            conn.execute(f"INSERT INTO Orders VALUES ({new_id}, {custid}, {bookid}, {saleprice}, '{today}')")
            st.success(f"주문 완료! (번호: {new_id})")
            st.dataframe(query(f"SELECT * FROM Orders WHERE orderid = {new_id}"))