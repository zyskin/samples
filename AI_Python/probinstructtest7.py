import openai
import math
import threading
import time

# Read the OpenAI API key from a file for security
with open("api_key.txt", "r") as file:
    openai.api_key = file.read().strip()

# Input parameters
input_text = "Write Python code to calculate factorial of a number.\n\n"
steps = 15  # Number of completion steps
max_attempts = 100  # Maximum number of sampling attempts per step
unique_token_threshold = 5000  # Target number of unique tokens per step
logprobs_limit = 100  # Number of logprobs requested in each API call
allow_duplicates = False  # Whether to allow duplicate tokens in the output
logprob_cutoff = -1000  # Only consider tokens with logprobs greater than this cutoff
most_likely_N = 20  # Number of most likely tokens to display on screen per step
full_completion_flag = True  # Whether to perform regular full completions after stepwise sampling
max_full_completions = 5  # Maximum number of full completions
stop_sampling = False  # Global flag to stop sampling when 'qqq' is pressed
listening_for_interrupt = True  # Flag to enable or disable interrupt listening

# File to track growing completion progress
completion_progress_file = "stepwise_completion.txt"
with open(completion_progress_file, "w") as progress_file:
    progress_file.write("Stepwise completion progress:\n\n")

# Function to convert logprobs to probabilities
def logprob_to_prob(logprob):
    return math.exp(logprob)

# Function to listen for keyboard input
def listen_for_stop():
    global stop_sampling, listening_for_interrupt
    while listening_for_interrupt:
        key = input("Press 'qqq' to stop sampling: ").strip()
        if key == 'qqq':
            stop_sampling = True
            break

# Single log file for all steps
steps_log_file = "steps_log.txt"
with open(steps_log_file, "w") as log_file:

    # Sampling logic
    for step in range(steps):
        print(f"Starting step {step + 1}...")

        unique_tokens = {}  # Dictionary to store tokens and their highest logprobs
        attempts = 0
        stop_sampling = False  # Reset stop_sampling for each step

        # Start keyboard listener before sampling
        listening_for_interrupt = True
        listener_thread = threading.Thread(target=listen_for_stop, daemon=True)
        listener_thread.start()

        while len(unique_tokens) < unique_token_threshold and attempts < max_attempts:
            if stop_sampling:
                print("Sampling stopped by user.")
                break

            attempts += 1
            time.sleep(0.2)

            # Make API call
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct-0914",
                prompt=input_text,
                max_tokens=1,  # Generate one token at a time
                logprobs=logprobs_limit,  # Request logprobs for the top tokens
                temperature=2.0,  # High temperature for variability
                n=1  # Single completion
            )

            # Extract tokens and logprobs
            tokens = response['choices'][0]['logprobs']['tokens']
            token_logprobs = response['choices'][0]['logprobs']['token_logprobs']

            # Add tokens and logprobs to the dictionary if they exceed the cutoff
            new_tokens = []
            for token, logprob in zip(tokens, token_logprobs):
                if logprob > logprob_cutoff:
                    new_tokens.append((token, logprob))
                    if token in unique_tokens:
                        # Update logprob if the new one is larger
                        if logprob > unique_tokens[token]:
                            unique_tokens[token] = logprob
                    else:
                        unique_tokens[token] = logprob

            # Print details of the attempt
            print(f"Attempt {attempts}: Collected {len(unique_tokens)} unique tokens so far.")
            log_file.write(f"Attempt {attempts}: Collected {len(unique_tokens)} unique tokens so far.\n")
            for token, logprob in new_tokens:
                print(f"  Received Token: {repr(token)}, Logprob: {logprob:.6f}")
                log_file.write(f"  Received Token: {repr(token)}, Logprob: {logprob:.6f}\n")

        # Stop keyboard listener after sampling
        listening_for_interrupt = False

        # Sort tokens by logprob in descending order
        sorted_tokens = sorted(unique_tokens.items(), key=lambda x: x[1], reverse=True)

        # Save results to a file
        output_file = f"step_{step + 1}_tokens.txt"
        with open(output_file, "w") as file:
            for token, logprob in sorted_tokens:
                file.write(f"{logprob:.6f} {repr(token)}\n")

        print(f"Step {step + 1} completed. Tokens saved to {output_file}.")
        log_file.write(f"Step {step + 1} completed. Tokens saved to {output_file}.\n")

        # Print the N most likely tokens for this step
        top_tokens_to_display = min(len(sorted_tokens), most_likely_N)
        print(f"Top {top_tokens_to_display} tokens for step {step + 1}:")
        log_file.write(f"Top {top_tokens_to_display} tokens for step {step + 1}:\n")
        for i, (token, logprob) in enumerate(sorted_tokens[:top_tokens_to_display]):
            print(f"  {i + 1}. Token: {repr(token)}, Logprob: {logprob:.6f}")
            log_file.write(f"  {i + 1}. Token: {repr(token)}, Logprob: {logprob:.6f}\n")

        # Offer to select a token
        selected = False
        while not selected:
            print(f"Please select a token by entering its number (1-{top_tokens_to_display}), or enter -1 to provide your own token:")
            selection = input().strip()

            if selection == "-1":
                custom_token = input("Enter your custom token: ").strip()
                most_likely_token = custom_token
                selected = True
            else:
                try:
                    selected_index = int(selection) - 1
                    if 0 <= selected_index < len(sorted_tokens[:top_tokens_to_display]):
                        most_likely_token = sorted_tokens[selected_index][0]
                        selected = True
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Invalid input. Please try again.")

        print(f"Selected token for step {step + 1}: {repr(most_likely_token)}")
        log_file.write(f"Selected token for step {step + 1}: {repr(most_likely_token)}\n")
        input_text += most_likely_token

        # Update progress in stepwise completion file
        with open(completion_progress_file, "a") as progress_file:
            progress_file.write(f"Step {step + 1}: {repr(most_likely_token)}\n")

    log_file.write(f"Final completion after step {step + 1}: {input_text}\n")

# Perform regular completion if the flag is True
if full_completion_flag:
    print("Performing regular full completions...")

    # File to save full completions
    full_completion_file = "full_completions.txt"

    with open(full_completion_file, "w") as file:
        for i in range(max_full_completions):
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct-0914",
                prompt=input_text,
                max_tokens=100,  # Allow up to 100 tokens per completion
                temperature=0.7,  # Moderate randomness
                n=1  # Single completion per call
            )

            # Extract and save the completion
            completion = response['choices'][0]['text'].strip()
            file.write(f"Completion {i + 1}:\n{completion}\n\n")
            print(f"Completion {i + 1}: {completion}")

    print(f"Full completions saved to {full_completion_file}.")

print("All tasks completed.")

