import argparse
import importlib.util
from pathlib import Path

from . import ansi, debugger


def parse_args():
    parser = argparse.ArgumentParser(
        description="A simple Python debugger and profiler that can generate animated visualizations of program flow."
    )

    parser.add_argument("file", metavar="FILE", help="Python file to debug or JSON file to replay")
    parser.add_argument(
        "-n",
        "--function",
        nargs="?",
        default="main",
        help="function to run from the given file (if applicable, default main)",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        nargs="?",
        metavar="OUTPUT",
        help="path to write JSON output file to (will be truncated/created if necessary)",
    )
    parser.add_argument(
        "-v",
        "--video",
        nargs="?",
        help="path to write a video representation of the program flow to (supports MP4, GIF, and WebP formats based on file extension)",
    )
    parser.add_argument(
        "-c", "--video-config", nargs="?", metavar="CONFIG", help="path to the TOML video output config",
    )
    parser.add_argument(
        "-a", "--args", nargs="*", default=[], metavar="ARGS", help="list of arguments to pass to the running program",
    )
    parser.add_argument(
        "-p",
        "--absolute-paths",
        default=False,
        action="store_true",
        help="use absolute paths instead of relative ones",
    )
    parser.add_argument(
        "-P",
        "--disable-live-profiler",
        default=False,
        action="store_true",
        help="disable live profiler output during execution",
    )

    return parser.parse_args()


def do_debug(args, mod):
    # Get the function here regardless of which path we took above
    func = getattr(mod, args.function, None)
    if func is None:
        # Check how many functions are present in the module
        func_syms = [sym for sym in dir(mod) if callable(getattr(mod, sym))]
        if len(func_syms) == 1:
            # Safe to assume that the user wanted this one if it's the only one
            f_sym = func_syms[0]
            func = getattr(mod, f_sym)
            print(ansi.yellow(f"Unable to find function '{args.function}', falling back to the only one: '{f_sym}'"))
            print()
        else:
            # Ambiguous if multiple, so bail out and let the user choose
            print(ansi.red(f"Unable to find function '{args.function}' and multiple are present; aborting."))
            return 1

    # Call the actual debugger with our parameters
    debugger.debug(
        func,
        args=[args.file or func.__code__.co_filename, *args.args],
        relative_paths=not args.absolute_paths,
        json_out_path=args.output_file,
        video_out_path=args.video,
        video_config=args.video_config,
        live_profiler_output=not args.disable_live_profiler,
    )
    return 0


def do_replay(args):
    debugger.replay(args.file, video_out_path=args.video, video_config=args.video_config)


def main():
    args = parse_args()

    # Use pathlib to get more info about the input file
    file_path = Path(args.file)
    if file_path.suffix == ".json":
        # JSON file means to replay, not debug
        return do_replay(args)
    else:
        # Load file as module and debug
        mod_name = Path(args.file).stem
        spec = importlib.util.spec_from_file_location(mod_name, args.file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        return do_debug(args, mod)
