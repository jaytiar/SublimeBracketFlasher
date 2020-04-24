import sublime
import sublime_plugin
import functools


def plugin_loaded():
    global settings
    settings = sublime.load_settings("BracketFlasher.sublime-settings")


class BracketFlasher(sublime_plugin.EventListener):
    """Event listener for highlighting bracket matches"""

    def on_modified(self, view):
        """Called whenever a view is modified."""
        # This is too slow if we use the _async version.

        if view.settings().get('is_widget', False):
            # Don't render in widget views
            return

        # Get various settings.
        global settings
        match_style = settings.get("match_scope", "comment")
        error_style = settings.get("error_scope", "invalid.illegal")
        backtrack_limit = settings.get("backtrack_limit", 100000)
        flash_time = settings.get("flash_time", 200)
        brackets = settings.get("brackets", [])

        start_location = view.sel()[0].begin() - 1
        bracket = view.substr(start_location)
        for b in brackets:
            if bracket == b["bracket"]:
                # We are to the right of a bracket.
                # Check this is a scope we're interested in.
                scope = view.scope_name(start_location)
                include = b["include"]
                exclude = b["exclude"]
                if (include and not any(i in scope for i in include)) or \
                   (exclude and any(e in scope for e in exclude)):
                    # Not a valid scope, try the next one.
                    continue

                partner = b["partner"]

                # Count backwards for matching brackets.
                count = 1
                location = start_location - 1
                while count > 0 and location >= 0 \
                        and (start_location - location) < backtrack_limit:
                    char = view.substr(location)
                    scope = view.scope_name(location)

                    # Ignore brackets at the wrong scope.
                    if (not include or any(i in scope for i in include)) and \
                       (not exclude or not any(e in scope for e in exclude)):
                        if char == bracket:
                            count += 1
                        elif char == partner:
                            count -= 1
                    location -= 1
                location += 1
                start_location += 1

                # If we got to the start of the file (or limit), it's an error.
                if count != 0:
                    style = error_style
                else:
                    style = match_style

                # Create the regions and set a timer to clear them again after
                # the timeout.
                view.add_regions("BracketFlasher" + str(start_location),
                                 [sublime.Region(location, start_location)],
                                 style)
                sublime.set_timeout_async(functools.partial(self.clear_regions,
                                                            view,
                                                            start_location),
                                          flash_time)
                break

    def clear_regions(self, view, loc):
        view.erase_regions("BracketFlasher" + str(loc))
