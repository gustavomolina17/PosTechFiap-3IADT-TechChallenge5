from datetime import datetime
from io import BytesIO
import re

import streamlit as st
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


def _processar_texto_formatado(texto):
    """
    Processa o texto para preservar a formatação original com quebras de linha e estrutura.
    """
    if not texto:
        return []

    # Dividir o texto em linhas
    linhas = texto.split('\n')
    elementos = []

    for linha in linhas:
        linha = linha.strip()
        if linha:
            # Verificar se é um título de seção (contém "–" ou ":")
            if '–' in linha and not linha.startswith(('S (', 'T (', 'R (', 'I (', 'D (', 'E (')):
                elementos.append(('titulo', linha))
            # Verificar se é uma seção principal (Ameaças:, Justificativa:, Mitigação:)
            elif linha.endswith(':') and linha in ['Ameaças:', 'Justificativa:', 'Mitigação:']:
                elementos.append(('secao', linha))
            # Verificar se é uma ameaça STRIDE
            elif re.match(r'^[A-Z] \([^)]+\)', linha):
                elementos.append(('ameaca', linha))
            # Verificar se é uma linha de mitigação (começa com •)
            elif linha.startswith('•'):
                elementos.append(('mitigacao', linha))
            else:
                elementos.append(('normal', linha))
        else:
            elementos.append(('espaco', ''))

    return elementos


def _gerar_relatorio_pdf(resultados_itens, descricao_componentes, resultados_fluxo, resultado_items,
                         resultado_flow):
    """
    Gera um relatório em PDF com todos os resultados da análise de vulnerabilidade.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1 * inch, bottomMargin=1 * inch)

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20
    )
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=12
    )
    normal_style = styles['Normal']
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )

    # Conteúdo do PDF
    story = []

    # Título
    story.append(Paragraph("Relatório de Análise de Vulnerabilidade em Arquitetura de Software", title_style))
    story.append(Spacer(1, 20))

    # Data e hora do relatório
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story.append(Paragraph(f"Relatório gerado em: {data_atual}", normal_style))
    story.append(Spacer(1, 20))

    # Componentes identificados
    story.append(Paragraph("📦 Componentes Identificados", heading_style))
    story.append(Paragraph("[", normal_style))
    if resultados_itens:
        for i, item in enumerate(resultados_itens):
            story.append(Paragraph(f'{i}:"{item}"', normal_style))
    else:
        story.append(Paragraph("Nenhum componente identificado.", normal_style))
    story.append(Paragraph("]", normal_style))
    story.append(Spacer(1, 15))

    # Descrição dos componentes
    story.append(Paragraph("🧠 Descrição dos Componentes", heading_style))
    if descricao_componentes:
        for componente, descricao in descricao_componentes.items():
            story.append(Paragraph(f"<b>{componente}</b>: {descricao}", normal_style))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Nenhuma descrição de componente disponível.", normal_style))
    story.append(Spacer(1, 15))

    # Fluxo da aplicação
    story.append(Paragraph("🔁 Fluxo da Aplicação", heading_style))
    if resultados_fluxo:
        if isinstance(resultados_fluxo, list):
            for fluxo in resultados_fluxo:
                if isinstance(fluxo, str):
                    story.append(Paragraph(fluxo, normal_style))
                    story.append(Spacer(1, 6))
        elif isinstance(resultados_fluxo, str):
            # Dividir por quebras de linha mantendo a estrutura
            linhas_fluxo = resultados_fluxo.split('\n')
            for linha in linhas_fluxo:
                linha = linha.strip()
                if linha:
                    story.append(Paragraph(linha, normal_style))
                    story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Nenhum fluxo identificado.", normal_style))
    story.append(Spacer(1, 15))

    # Nova página para análises de vulnerabilidade
    story.append(PageBreak())

    # Análise de vulnerabilidade por item
    story.append(Paragraph("🔍 Análise de Vulnerabilidade por Item", heading_style))

    # Texto introdutório
    intro_text = """A seguir está uma análise STRIDE "item–a–item" para cada componente listado. Para cada um, você encontrará:

• Principais ameaças STRIDE
• Justificativa técnica
• Recomendações de mitigação"""

    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 15))

    if resultado_items:
        if isinstance(resultado_items, str):
            # Processar o texto formatado
            elementos = _processar_texto_formatado(resultado_items)

            for tipo, conteudo in elementos:
                if tipo == 'titulo':
                    story.append(Paragraph(f"<b>{conteudo}</b>", subheading_style))
                elif tipo == 'secao':
                    story.append(Paragraph(f"<b>{conteudo}</b>", bold_style))
                elif tipo == 'ameaca':
                    story.append(Paragraph(conteudo, normal_style))
                elif tipo == 'mitigacao':
                    story.append(Paragraph(conteudo, normal_style))
                elif tipo == 'normal':
                    story.append(Paragraph(conteudo, normal_style))
                elif tipo == 'espaco':
                    story.append(Spacer(1, 8))
        else:
            # Se for uma estrutura de dados, processar cada item
            for item in resultado_items:
                story.append(Paragraph(str(item), normal_style))
                story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("Nenhuma análise de item disponível.", normal_style))

    story.append(Spacer(1, 20))

    # Análise de vulnerabilidade do fluxo de dados
    story.append(Paragraph("🔍 Análise de Vulnerabilidade do Fluxo de Dados", heading_style))

    # Texto introdutório
    intro_fluxo_text = """Seguem as principais cadeias de fluxo de dados do seu ambiente e, para cada uma, as ameaças STRIDE, justificativas técnicas e recomendações de mitigação."""

    story.append(Paragraph(intro_fluxo_text, normal_style))
    story.append(Spacer(1, 15))

    if resultado_flow:
        if isinstance(resultado_flow, str):
            # Processar o texto formatado
            elementos = _processar_texto_formatado(resultado_flow)

            for tipo, conteudo in elementos:
                if tipo == 'titulo':
                    story.append(Paragraph(f"<b>{conteudo}</b>", subheading_style))
                elif tipo == 'secao':
                    story.append(Paragraph(f"<b>{conteudo}</b>", bold_style))
                elif tipo == 'ameaca':
                    story.append(Paragraph(conteudo, normal_style))
                elif tipo == 'mitigacao':
                    story.append(Paragraph(conteudo, normal_style))
                elif tipo == 'normal':
                    story.append(Paragraph(conteudo, normal_style))
                elif tipo == 'espaco':
                    story.append(Spacer(1, 8))
        else:
            # Se for uma lista ou estrutura de dados, processar cada fluxo
            for fluxo in resultado_flow:
                story.append(Paragraph(str(fluxo), normal_style))
                story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("Nenhuma análise de fluxo disponível.", normal_style))

    # Construir o PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


@st.fragment()
def pdf_button(resultados_itens, descricao_componentes, resultados_fluxo, resultado_items,
               resultado_flow):
    if st.button("Gerar PDF do Relatório"):
        with st.spinner('Gerando PDF... Por favor, aguarde.'):
            pdf_buffer = _gerar_relatorio_pdf(
                resultados_itens=resultados_itens,
                descricao_componentes=descricao_componentes,
                resultados_fluxo=resultados_fluxo,
                resultado_items=resultado_items,
                resultado_flow=resultado_flow
            )
            st.download_button(
                label="Baixar PDF",
                data=pdf_buffer,
                file_name="relatorio_vulnerabilidades.pdf",
                mime="application/pdf"
            )
        st.success("PDF gerado com sucesso!", icon="✅")