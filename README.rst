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




problems
---------------------------------------------

UnicodeDecodeError: 'utf-8' codec can't decode byte 0x82 in position 0: invalid start byte
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

.. code-block::


    Traceback (most recent call last):
    File "/home/deploy/envs/default/bin/cqh_tail", line 8, in <module>
        sys.exit(main())
    File "/home/deploy/envs/default/lib/python3.6/site-packages/cqh_tail/run.py", line 318, in main
        w = LogWatcher(pattern, tail_lines=count, callback=echo)
    File "/home/deploy/envs/default/lib/python3.6/site-packages/cqh_tail/run.py", line 66, in __init__
        self._callback(file.name, lines)
    File "/home/deploy/envs/default/lib/python3.6/site-packages/cqh_tail/run.py", line 313, in echo
        line = line.decode(convert_args.encode)
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0x82 in position 0: invalid start byte
