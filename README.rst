cqh_tail
=============================================

python tail

copy from `activestate <http://code.activestate.com/recipes/577968-log-watcher-tail-f-log/>`_


Usage
-------------------------------------------------

watch dir
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

.. code-block::

    cqh_tail --pattern=~/**/*.log

watch dir and filter
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

.. code-block::

    cqh_tail --pattern=~/**/*.log --line-filter="\.general/"

