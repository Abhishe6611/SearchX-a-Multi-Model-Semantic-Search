"""
Simplified Database Content Inspector - Save to JSON
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import json
import re
from typing import List, Dict
from datetime import datetime

class DatabaseInspector:
    def __init__(self, db_path: str = "searchx.db"):
        self.db_path = db_path

    def preprocess_text_for_bm25(self, text: str) -> List[str]:
        """Same preprocessing as hybrid search service"""
        if not text:
            return []

        # Convert to lowercase and remove special characters
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Tokenize
        tokens = text.split()

        # Remove stop words but preserve important terms
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'from', 'this', 'that', 'these', 'those', 'is',
            'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'do', 'does',
            'did', 'a', 'an'
        }

        # Preserve legal/government terms
        preserved_terms = {
            'article', 'section', 'paragraph', 'clause', 'act', 'policy',
            'regulation', 'amendment', 'compliance', 'law', 'legal'
        }

        filtered_tokens = []
        for token in tokens:
            if len(token) >= 2:
                if token not in stop_words or token in preserved_terms:
                    filtered_tokens.append(token)

        return filtered_tokens

    def get_all_documents(self) -> List[Dict]:
        """Retrieve all processed documents from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, original_filename, extracted_text, file_type,
                   upload_date, has_embedding, processing_status
            FROM media_files
            WHERE processing_status = 'SUCCESS'
            AND extracted_text IS NOT NULL
            ORDER BY upload_date DESC
        """)

        documents = []
        for row in cursor.fetchall():
            doc = {
                'id': row[0],
                'filename': row[1],
                'extracted_text': row[2],
                'file_type': row[3],
                'upload_date': row[4],
                'has_embedding': bool(row[5]),
                'processing_status': row[6]
            }
            documents.append(doc)

        conn.close()
        return documents

    def analyze_document_keywords(self, doc: Dict) -> Dict:
        """Analyze keywords and text statistics for a document"""
        text = doc['extracted_text']
        keywords = self.preprocess_text_for_bm25(text)

        # Calculate statistics
        total_words = len(text.split()) if text else 0
        unique_keywords = len(set(keywords))
        keyword_density = len(keywords) / total_words if total_words > 0 else 0

        # Most frequent keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        top_keywords = keyword_counts.most_common(10)

        return {
            'doc_info': {
                'id': doc['id'],
                'filename': doc['filename'],
                'file_type': doc['file_type'],
                'upload_date': doc['upload_date']
            },
            'text_stats': {
                'total_length': len(text) if text else 0,
                'total_words': total_words,
                'processed_keywords': len(keywords),
                'unique_keywords': unique_keywords,
                'keyword_density': round(keyword_density, 3)
            },
            'extracted_text': text,
            'sample_text': text[:300] + '...' if text and len(text) > 300 else text,
            'all_keywords': keywords,
            'top_keywords': top_keywords,
            'government_terms': [kw for kw in keywords if kw in [
                'government', 'policy', 'regulation', 'compliance', 'legal',
                'article', 'section', 'amendment', 'act', 'law', 'document'
            ]]
        }

    def generate_report(self) -> Dict:
        """Generate comprehensive keyword and text analysis report"""
        documents = self.get_all_documents()

        if not documents:
            return {
                'status': 'No documents found',
                'total_docs': 0,
                'documents': []
            }

        # Analyze each document
        analyzed_docs = []
        all_keywords = []

        for doc in documents:
            analysis = self.analyze_document_keywords(doc)
            analyzed_docs.append(analysis)
            all_keywords.extend(analysis['all_keywords'])

        # Global keyword statistics
        from collections import Counter
        global_keyword_counts = Counter(all_keywords)
        top_global_keywords = global_keyword_counts.most_common(20)

        return {
            'status': 'Success',
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_documents': len(documents),
                'total_keywords_extracted': len(all_keywords),
                'unique_keywords_global': len(set(all_keywords)),
                'avg_keywords_per_doc': round(len(all_keywords) / len(documents), 1)
            },
            'top_global_keywords': top_global_keywords,
            'documents': analyzed_docs
        }

def main():
    """Main execution function"""
    inspector = DatabaseInspector()

    try:
        print("Analyzing database content...")
        report = inspector.generate_report()

        if report['status'] != 'Success':
            print(f"Error: {report['status']}")
            return

        # Save detailed report to JSON file
        with open('keyword_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("Analysis complete! Results saved to 'keyword_analysis_report.json'")

        # Display summary
        summary = report['summary']
        print(f"\nSUMMARY:")
        print(f"- Total Documents: {summary['total_documents']}")
        print(f"- Total Keywords: {summary['total_keywords_extracted']}")
        print(f"- Unique Keywords: {summary['unique_keywords_global']}")
        print(f"- Average Keywords per Document: {summary['avg_keywords_per_doc']}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()