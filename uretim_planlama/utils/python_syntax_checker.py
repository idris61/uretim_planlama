"""
Python Syntax ve Girinti Kontrol Aracı

Kullanım:
	bench --site sitename execute uretim_planlama.utils.python_syntax_checker.check_all_python_files
"""

import ast
from pathlib import Path

import frappe


def check_python_file(file_path):
	"""Tek bir Python dosyasını kontrol eder"""
	errors = []
	
	try:
		with open(file_path, 'r', encoding='utf-8') as f:
			source_code = f.read()
		
		# Syntax kontrolü
		try:
			ast.parse(source_code)
		except SyntaxError as e:
			errors.append({
				'type': 'SyntaxError',
				'line': e.lineno,
				'msg': str(e.msg),
				'text': e.text
			})
		except IndentationError as e:
			errors.append({
				'type': 'IndentationError',
				'line': e.lineno,
				'msg': str(e.msg),
				'text': e.text
			})
		
		# Tab/Space karışımı kontrolü
		lines = source_code.split('\n')
		for i, line in enumerate(lines, 1):
			if line.strip() and not line.strip().startswith('#'):
				leading_ws = line[:len(line) - len(line.lstrip())]
				if '\t' in leading_ws and ' ' in leading_ws:
					errors.append({
						'type': 'MixedIndentation',
						'line': i,
						'msg': 'Tab ve space karışık kullanılmış',
						'text': line[:50]
					})
		
	except Exception as e:
		errors.append({
			'type': 'FileError',
			'line': 0,
			'msg': f'Dosya okunamadı: {str(e)}',
			'text': ''
		})
	
	return errors


@frappe.whitelist()
def check_all_python_files(app_name="uretim_planlama"):
	"""Tüm Python dosyalarını kontrol eder"""
	app_path = frappe.get_app_path(app_name)
	python_files = list(Path(app_path).rglob("*.py"))
	
	results = {
		'total_files': len(python_files),
		'files_with_errors': 0,
		'total_errors': 0,
		'errors_by_file': {}
	}
	
	print(f"\n{'='*70}")
	print(f"🔍 PYTHON SYNTAX KONTROLÜ: {app_name}")
	print(f"{'='*70}\n")
	print(f"📁 Toplam {len(python_files)} Python dosyası taranıyor...\n")
	
	for py_file in python_files:
		if 'migrations' in str(py_file) or '__pycache__' in str(py_file):
			continue
		
		errors = check_python_file(py_file)
		
		if errors:
			results['files_with_errors'] += 1
			results['total_errors'] += len(errors)
			
			relative_path = py_file.relative_to(app_path)
			results['errors_by_file'][str(relative_path)] = errors
			
			print(f"❌ {relative_path}")
			for error in errors:
				print(f"   {error['type']} (Satır {error['line']}): {error['msg']}")
				if error.get('text'):
					print(f"      {error['text'].strip()}")
			print()
	
	print(f"\n{'='*70}")
	print(f"📊 ÖZET")
	print(f"{'='*70}")
	print(f"✅ Temiz Dosya: {results['total_files'] - results['files_with_errors']}")
	print(f"❌ Hatalı Dosya: {results['files_with_errors']}")
	print(f"🐛 Toplam Hata: {results['total_errors']}")
	print(f"{'='*70}\n")
	
	return results
