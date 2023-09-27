build: # Build all HTML to ../blog_html
	poetry run sai build -c -o ../blog_html

serve: build
	poetry run sai serve -o ../blog_html