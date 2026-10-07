# Run the skills CLI with Deno.
[positional-arguments]
skills *args:
    deno run -A --no-lock npm:skills "$@"
