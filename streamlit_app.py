import sqlite3
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Troca de Óleo", page_icon="🛢️", layout="wide")

# --- BANCO DE DADOS ---
def conectar_bd():
    return sqlite3.connect('troca_de_oleo.db')

def criar_tabelas():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            produto_id INTEGER,
            quantidade INTEGER,
            total REAL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    conn.commit()
    conn.close()

criar_tabelas()

# --- INTERFACE E NAVEGAÇÃO ---
st.title("🛢️ Gerenciador de Estoque e Vendas")

# Menu na barra lateral
menu = st.sidebar.radio("Navegação", ["📦 Realizar Venda", "➕ Cadastrar / Repor Óleo", "📊 Histórico de Vendas"])

# --- TELA 1: REALIZAR VENDA ---
if menu == "📦 Realizar Venda":
    st.header("Realizar Venda")
    
    conn = conectar_bd()
    produtos_df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()

    if produtos_df.empty:
        st.warning("Nenhum óleo cadastrado no estoque ainda.")
    else:
        # Mostra o estoque em formato visual bonito
        st.subheader("Estoque Atual")
        st.dataframe(produtos_df, use_container_width=True)

        col1, col2 = st.columns(2)
        
        with col1:
            # Lista suspensa para escolher o produto
            opcoes_produtos = {f"{row['id']} - {row['nome']} (Estoque: {row['quantidade']})": row['id'] for _, row in produtos_df.iterrows()}
            produto_selecionado = st.selectbox("Selecione o Óleo:", list(opcoes_produtos.keys()))
            id_produto = opcoes_produtos[produto_selecionado]

        with col2:
            qtd_venda = st.number_input("Quantidade a Vender:", min_value=1, step=1)

        if st.button("Confirmar Venda", type="primary"):
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # Pega dados atuais do produto
            cursor.execute("SELECT quantidade, preco, nome FROM produtos WHERE id = ?", (id_produto,))
            qtd_atual, preco, nome = cursor.fetchone()

            if qtd_venda > qtd_atual:
                st.error("Quantidade solicitada é maior que o estoque disponível!")
            else:
                nova_qtd = qtd_atual - qtd_venda
                total_venda = qtd_venda * preco

                # Atualiza estoque e insere venda
                cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_qtd, id_produto))
                cursor.execute("INSERT INTO vendas (produto_id, quantidade, total) VALUES (?, ?, ?)", (id_produto, qtd_venda, total_venda))
                conn.commit()
                
                st.success(f"Venda de {qtd_venda}x {nome} realizada com sucesso! Total: R$ {total_venda:.2f}")
                st.rerun()
            conn.close()

# --- TELA 2: CADASTRAR / REPOR ---
elif menu == "➕ Cadastrar / Repor Óleo":
    st.header("Cadastrar Novo Óleo ou Atualizar")

    with st.form("form_cadastro"):
        nome = st.text_input("Nome / Especificação do Óleo (ex: Mobil 5W30 Sintético)")
        quantidade = st.number_input("Quantidade Inicial / Adicionada:", min_value=1, step=1)
        preco = st.number_input("Preço de Venda (R$):", min_value=0.0, format="%.2f")
        
        btn_salvar = st.form_submit_button("Salvar no Estoque")

    if btn_salvar:
        if nome:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO produtos (nome, quantidade, preco) VALUES (?, ?, ?)", (nome, quantidade, preco))
            conn.commit()
            conn.close()
            st.success(f"Óleo '{nome}' adicionado com sucesso!")
        else:
            st.error("Por favor, preencha o nome do produto.")

# --- TELA 3: HISTÓRICO DE VENDAS ---
elif menu == "📊 Histórico de Vendas":
    st.header("Histórico de Vendas")
    
    conn = conectar_bd()
    query = '''
        SELECT v.id, v.data, p.nome as produto, v.quantidade, v.total 
        FROM vendas v 
        JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.data DESC
    '''
    vendas_df = pd.read_sql_query(query, conn)
    conn.close()

    if vendas_df.empty:
        st.info("Nenhuma venda registrada até o momento.")
    else:
        st.dataframe(vendas_df, use_container_width=True)
        faturamento_total = vendas_df['total'].sum()
        st.metric(label="Faturamento Total", value=f"R$ {faturamento_total:.2f}")


