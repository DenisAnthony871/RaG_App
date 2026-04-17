import pytest
from unittest.mock import patch, MagicMock
from tools import retriever_tool

def test_retriever_tool_no_results():
    with patch('tools.retriever') as mock_retriever:
        mock_retriever.invoke.return_value = []
        result = retriever_tool.invoke("test query")
        assert result == "No results found"

def test_retriever_tool_single_result():
    with patch('tools.retriever') as mock_retriever:
        doc1 = MagicMock()
        doc1.page_content = "Single document content"
        mock_retriever.invoke.return_value = [doc1]
        
        result = retriever_tool.invoke("test query")
        assert result == "[1] Single document content"

def test_retriever_tool_multiple_results():
    with patch('tools.retriever') as mock_retriever:
        doc1 = MagicMock()
        doc1.page_content = "Document 1"
        doc2 = MagicMock()
        doc2.page_content = "Document 2"
        mock_retriever.invoke.return_value = [doc1, doc2]
        
        result = retriever_tool.invoke("test query")
        assert "[1] Document 1" in result
        assert "[2] Document 2" in result
        assert "[3]" not in result

def test_retriever_tool_five_results():
    with patch('tools.retriever') as mock_retriever:
        docs = []
        for i in range(1, 6):
            doc = MagicMock()
            doc.page_content = f"Doc {i}"
            docs.append(doc)
            
        mock_retriever.invoke.return_value = docs
        result = retriever_tool.invoke("test query")
        
        for i in range(1, 6):
            assert f"[{i}] Doc {i}" in result
        assert "[6]" not in result

def test_retriever_tool_hard_cap():
    with patch('tools.retriever') as mock_retriever:
        docs = []
        for i in range(1, 10):
            doc = MagicMock()
            doc.page_content = f"Doc {i}"
            docs.append(doc)
            
        mock_retriever.invoke.return_value = docs
        result = retriever_tool.invoke("test query")
        
        assert "[5] Doc 5" in result
        assert "[6] Doc 6" not in result
        assert "[6]" not in result

def test_retriever_tool_query_forwarded():
    with patch('tools.retriever') as mock_retriever:
        mock_retriever.invoke.return_value = []
        
        query = "forward me verbatim"
        retriever_tool.invoke(query)
        
        mock_retriever.invoke.assert_called_once_with(query)
