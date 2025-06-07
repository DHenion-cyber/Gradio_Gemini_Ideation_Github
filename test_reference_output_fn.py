from evals.registry.completion_fns.reference_output import ReferenceOutputCompletionFn
import json

SAMPLES_FILE = "evals/sample_data/coaching_convos.jsonl"

try:
    print(f"Attempting to initialize ReferenceOutputCompletionFn with {SAMPLES_FILE}...")
    completion_fn = ReferenceOutputCompletionFn(samples_jsonl=SAMPLES_FILE)
    print("Initialization successful.")
    print(f"Number of samples loaded: {len(completion_fn.samples)}")

    if len(completion_fn.samples) > 0:
        print("\nFirst sample:")
        print(json.dumps(completion_fn.samples[0], indent=2))

        print("\nCalling completion_fn for the first sample...")
        result1 = completion_fn(prompt="dummy_prompt_1")
        print(f"Result 1: {result1}")

        if len(completion_fn.samples) > 1:
            print("\nCalling completion_fn for the second sample...")
            result2 = completion_fn(prompt="dummy_prompt_2")
            print(f"Result 2: {result2}")
        else:
            print("\nNot enough samples for a second call.")
    else:
        print("\nNo samples loaded, cannot test __call__.")

except Exception as e:
    print(f"\nAn error occurred: {e}")
    import traceback
    traceback.print_exc()

print("\nTest script finished.")