clean: clean-build clean-pyc

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr .pytest_cache/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

install: clean ## install the package to the active Python's site-packages
	python setup.py install

test: test-py2 test-py3
test-py2: test-setpy2 test-run
test-py3: test-setpy3 test-run
test-setpy3:
	pyenv global 3.6.5
test-setpy2:
	pyenv global 2.7.6
test-run: install
	python -m pytest

install-pyenv:
	#executing multiple times will fail upon cloning of git repo into a preexisting directory
	#caution multiple successful executions will clutter ~/.bashrc and ~/.bash_profile
	apt-get install -y git
	git clone https://github.com/pyenv/pyenv.git ~/.pyenv
	echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
	echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
	echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bash_profile
	echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
	echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
	echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc
	pyenv install 2.7.6
	pyenv install 3.6.5

clean-deploy:
	rm -fr examples/
	rm -fr tests/
	rm -fr README.*
	rm -fr changelog.rst
	rm -fr pytest.ini
	rm -fr .pytest_cache/
	find . -name '__pycache__' -exec rm -fr {} +
