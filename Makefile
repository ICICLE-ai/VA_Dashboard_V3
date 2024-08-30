# Makefile for Visual Analytics Dashboard V1 (front+back)

# Colors in echos: https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux
# Colors
BLACK=\033[0;30m
RED=\033[0;31m
GREEN=\033[0;32m
ORANGE=\033[0;33m
BLUE=\033[0;34m
PURPLE=\033[0;35m
CYAN=\033[0;36m
GRAY=\033[1;30m

# Light colors
WHITE=\033[1;37m
LRED=\033[1;31m
LGREEN=\033[1;32m
YELLOW=\033[1;33m
LBLUE=\033[1;34m
LPURPLE=\033[1;35m
LCYAN=\033[1;36m
LGRAY=\033[0;37m

# No color
NC=\033[0m

.ONESHELL: down
.PHONY: down clean help

# TAG to use for image
# options: "dev" | "prod" | *
# default: "dev"
export TAG := dev


# Got from: https://stackoverflow.com/a/59087509
help:
	@grep -B1 -E "^[a-zA-Z0-9_-]+\:([^\=]|$$)" Makefile \
	| grep -v -- -- \
	| sed 'N;s/\n/###/' \
	| sed -n 's/^#: \(.*\)###\(.*\):.*/\2###\1/p' \
	| column -t  -s '###'

# Builds locally and sets correct tag.
# We set base_request_url here for local dev via sed.
#: Build front and backend images
build: vars
	@echo "Makefile: $(GREEN)build$(NC)"
	@echo "  🔨 : Building backend Django image."
	@echo ""
	docker build -t va3-backend:$$TAG backend/.
	@echo ""
	@echo "  🔨 : Building frontend Vite image."
	@echo ""	
	docker build -t va3-frontend:$$TAG frontend/.
	@echo ""


# Starts the frontend and backend.
#: Deploy service
up: build
	@echo "Makefile: $(GREEN)up$(NC)"
	@echo "  🔥 : Running burnup."
	@echo ""
	docker compose up -d
	@echo ""


# Ends all active k8 containers needed for pods
#: Burndown service
down:
	@echo "Makefile: $(GREEN)down$(NC)"
	@echo "  🔥 : Running burndown."
	@echo ""
	docker compose down 
	@echo ""


# Test setting of environment variables
#: Lists vars
vars:
	@echo "Makefile: $(GREEN)vars$(NC)"	
	echo "  ℹ️  tag:            $(LCYAN)$(TAG)$(NC)"
	echo "  🦁  frontend:       $(LCYAN)http://localhost:5173$(NC)"
	echo "  🦁  backend:        $(LCYAN)http://localhost:8000/api$(NC)"