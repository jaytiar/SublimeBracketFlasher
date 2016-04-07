import sublime
import sublime_plugin
import functools


def plugin_loaded():
    global settings
    settings = sublime.load_settings("BracketFlasher.sublime-settings")


class BracketFlasher(sublime_plugin.EventListener):
    """Event listener for highlighting bracket matches"""
    PAIRS = {
        ")": "(",
        "]": "[",
        "}": "{"
    }

    def on_modified(self, view):
        """Called whenever a view is modified."""
        # This is too slow if we use the _async version.

        # Get various settings.
        global settings
        match_style = settings.get("match_scope", "comment")
        error_style = settings.get("error_scope", "invalid.illegal")
        backtrack_limit = settings.get("backtrack_limit", 100000)
        flash_time = settings.get("flash_time", 200)

        start_location = view.sel()[0].begin() - 1
        scope = view.scope_name(start_location)
        if "comment" in scope or "string" in scope:
            return
        bracket = view.substr(start_location)
        if bracket in self.PAIRS.keys():
            # We are to the right of a bracket.
            partner = self.PAIRS[bracket]

            # Count backwards for matching brackets.
            count = 1
            location = start_location - 1
            while count > 0 and location >= 0 \
                    and (start_location - location) < backtrack_limit:
                char = view.substr(location)
                scope = view.scope_name(location)
                # Ignore non-code brackets.
                if "comment" not in scope and "string" not in scope:
                    if char == bracket:
                        count += 1
                    elif char == partner:
                        count -= 1
                location -= 1
            location += 1
            start_location += 1

            # If we got to the start of the file with no match, it's an error.
            if count != 0:
                style = error_style
            else:
                style = match_style

            view.add_regions("BracketFlasher" + str(start_location),
                             [sublime.Region(location, start_location)],
                             style)
            sublime.set_timeout_async(functools.partial(self.clear_regions,
                                                        view,
                                                        start_location),
                                      flash_time)

    def clear_regions(self, view, loc):
        view.erase_regions("BracketFlasher" + str(loc))
