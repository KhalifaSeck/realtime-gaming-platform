.PHONY: help up down restart grafana-gen grafana-deploy full-stack

# ============================================================
# Aliases pour le pipeline batch et l'observability.
# ============================================================

help:
	@echo Commandes disponibles :
	@echo   make up               - docker compose up -d (tout le stack)
	@echo   make down             - docker compose down
	@echo   make grafana-gen      - regenere les JSON dashboards Grafana
	@echo   make grafana-deploy   - grafana-gen + restart Grafana
	@echo   make full-stack       - up + grafana-gen (setup complet)

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

grafana-gen:
	cd observability/grafana/dashboards_as_code && python generate_all.py

grafana-deploy: grafana-gen
	docker compose restart grafana

full-stack: up grafana-gen
	@echo Stack + dashboards deployes. UI : http://localhost:3000 (admin/rtgaming)