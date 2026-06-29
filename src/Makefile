include .env
export

API_HOST ?= 0.0.0.0
API_PORT ?= 9887

API_SRC=./api
TRAIN_SRC=./train

FRONTEND_SRC=./frontend
DESKTOP_SRC=$(FRONTEND_SRC)/desktop

.PHONY: run-api run-dev-api run-desktop api-dependencies train-dependencies frontend-desktop-dependencies
run-desktop:
	cd $(DESKTOP_SRC) && python3 main.py

run-api:
	cd $(API_SRC) && python3 main.py --host $(API_HOST) --port $(API_PORT)

run-dev-api:
	cd $(API_SRC) && uvicorn main:app --reload --host $(API_HOST) --port $(API_PORT)

api-dependencies:
	cd $(API_SRC) && pip3 install -r requirements.txt

frontend-desktop-dependencies:
	cd $(DESKTOP_SRC) && pip3 install -r requirements.txt
