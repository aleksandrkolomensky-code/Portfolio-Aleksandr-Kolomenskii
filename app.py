import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Banco Plata - Engineering Operations Dashboard", layout="wide")

st.title("📊 Платформа анализа инженерной эффективности конвейера поставки")
st.markdown("---")

# 1. Загрузка данных
@st.cache_data
def load_data():
    users = pd.read_csv('users.csv')
    issues = pd.read_csv('issues.csv')
    changelogs = pd.read_csv('changelogs.csv')
    return users, issues, changelogs

try:
    df_users, df_issues, df_changelogs = load_data()
    
    # Используем left join, чтобы не терять данные при фильтрации
    df_merged = df_changelogs.merge(df_issues, on='issue_id', how='left')
    df_merged = df_merged.merge(df_users, left_on='assignee_id', right_on='user_id', how='left')
    
    # Заполняем пропуски дефолтными значениями, если они есть
    df_merged['squad'] = df_merged['squad'].fillna('Other')
    df_merged['issue_type'] = df_merged['issue_type'].fillna('Story')
    
    # ИНТЕРФЕЙС: Боковая панель фильтров
    st.sidebar.header("🎯 Фильтры конвейера")
    
    squad_options = sorted(list(df_merged['squad'].unique()))
    selected_squad = st.sidebar.multiselect(
        "Выбор Команды (Squad):", 
        options=squad_options, 
        default=squad_options
    )
    
    type_options = sorted(list(df_merged['issue_type'].unique()))
    selected_type = st.sidebar.multiselect(
        "Тип задачи (Issue Type):", 
        options=type_options, 
        default=type_options
    )
    
    # Фильтрация датасета
    df_filtered = df_merged[
        (df_merged['squad'].isin(selected_squad)) & 
        (df_merged['issue_type'].isin(selected_type))
    ]
    
    # РАСЧЕТЫ: Flow Efficiency
    active_statuses = ['Analysis', 'In Progress', 'Code Review', 'QA In Progress']
    
    total_active = df_filtered[df_filtered['from_status'].isin(active_statuses)]['hours_spent'].sum()
    total_wait = df_filtered[~df_filtered['from_status'].isin(active_statuses)]['hours_spent'].sum()
    
    flow_efficiency = (total_active / (total_active + total_wait)) * 100 if (total_active + total_wait) > 0 else 0
    
    # ВЕРХНИЕ KPI КАРТОЧКИ
    col1, col2, col3 = st.columns(3)
    col1.metric("Эффективность потока (Flow Efficiency)", f"{flow_efficiency:.2f}%")
    col2.metric("Активное время работы (Active Time)", f"{total_active:,.1f} ч")
    col3.metric("Время простоев в очередях (Wait Time)", f"{total_wait:,.1f} ч")
    
    st.markdown("---")
    
    # СЕКЦИЯ ГРАФИКОВ
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("⏳ Распределение времени ожидания по очередям")
        wait_stages = ['Ready for Dev', 'Ready for Code Review', 'Ready for QA', 'Ready for Release']
        df_wait = df_filtered[df_filtered['from_status'].isin(wait_stages)]
        df_wait_grouped = df_wait.groupby('from_status')['hours_spent'].sum().reset_index()
        
        fig_bar = px.bar(
            df_wait_grouped, 
            x='from_status', 
            y='hours_spent',
            labels={'from_status': 'Статус очереди', 'hours_spent': 'Суммарный простой (часы)'},
            color='from_status',
            color_discrete_sequence=px.colors.sequential.Oranges_r
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_chart2:
        st.subheader("👥 Сравнение эффективности команд")
        squad_data = []
        for squad in selected_squad:
            df_sq = df_filtered[df_filtered['squad'] == squad]
            act = df_sq[df_sq['from_status'].isin(active_statuses)]['hours_spent'].sum()
            wt = df_sq[~df_sq['from_status'].isin(active_statuses)]['hours_spent'].sum()
            eff = (act / (act + wt)) * 100 if (act + wt) > 0 else 0
            squad_data.append({"Команда": squad, "Эффективность (%)": round(eff, 2)})
            
        fig_squad = px.bar(
            pd.DataFrame(squad_data), 
            x='Команда', 
            y='Эффективность (%)',
            range_y=[0, 100],
            color='Эффективность (%)',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig_squad, use_container_width=True)

except Exception as e:
    st.error(f"Не удалось загрузить данные. Проверьте файлы в корневой папке. Ошибка: {e}")
