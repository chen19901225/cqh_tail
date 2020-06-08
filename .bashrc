proj_name="cqh_tail"
alias tryl='python ${proj_name}/run.py --level=debug --conf=example.json'
alias try='cqh_tail --pattern=/home/vagrant/logs/*.log'
alias try1="python -m cqh_tail --pattern='/home/vagrant/logs/*.log'"
alias first_build='python3 setup.py sdist bdist_wheel'
alias build='rm dist/* && rm build/* -rf && python3 setup.py sdist bdist_wheel'

alias install='pip install -U dist/${proj_name}-*-py*'
alias bi='build && install'
alias uninstall='pip uninstall ${proj_name} -y'
alias publish='twine upload dist/*'
alias c-push="inv c-push"