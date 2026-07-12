(no RUN_REPORT.md — rc=1)

## stdout


## stderr
Traceback (most recent call last):
  File "/rebase/.venv/bin/omni-copilot", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/rebase/vllm-omni-copilot/src/omni_copilot/cli/entry.py", line 89, in main
    code = _handle_line(copilot, args.prompt, args.yes, args.plan_only)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/vllm-omni-copilot/src/omni_copilot/cli/entry.py", line 39, in _handle_line
    results = parse_intents(line, llm=copilot.llm,
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/vllm-omni-copilot/src/omni_copilot/intent.py", line 66, in parse_intents
    return [parse_intent(text, llm=llm, default_repo=default_repo, model=model)]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/vllm-omni-copilot/src/omni_copilot/intent.py", line 55, in parse_intent
    return _parse_llm(text, llm, default_repo, model)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/vllm-omni-copilot/src/omni_copilot/intent.py", line 101, in _parse_llm
    reply = llm.create(system=_LLM_SYSTEM,
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/vllm-omni-copilot/src/omni_copilot/llm.py", line 107, in create
    resp = self._client.messages.create(**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/.venv/lib/python3.12/site-packages/anthropic/_utils/_utils.py", line 294, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/.venv/lib/python3.12/site-packages/anthropic/resources/messages/messages.py", line 1003, in create
    return self._post(
           ^^^^^^^^^^^
  File "/rebase/.venv/lib/python3.12/site-packages/anthropic/_base_client.py", line 1374, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/rebase/.venv/lib/python3.12/site-packages/anthropic/_base_client.py", line 1147, in request
    raise self._make_status_error_from_response(err.response) from None
anthropic.APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}
