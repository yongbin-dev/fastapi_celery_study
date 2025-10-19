.PHONY: install run clean

install:
	pip install .

run:
	uvicorn app.main:app --reload

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
