import readline
import logging
import tempfile


LOG_FILENAME = tempfile.NamedTemporaryFile().name #'/tmp/completer.log'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )

class SimpleCompleter(object):
    match_index = None
    default = ''
    def __init__(self, parsername, options, default=''):
        #options = sites_dic.keys()
        options = [ w for w in options
            if w.startswith(default) ]
        self.options = sorted(options)
        self.default = default
        self.parsername = parsername
        # Register our completer function
        #readline.set_completer(SimpleCompleter(['start', 'stop', 'list', 'print']).complete)
        readline.set_completer(self.complete)
        # Use the tab key for completion
        readline.parse_and_bind('tab: complete')
        return

    def complete(self, text, state):
        response = None
        if text:
            if self.default:
                text = self.default + text
                #self.default = ''
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [s
                                for s in self.options
                                if s and s.startswith(text)]
            else:
                self.matches = self.options[:]

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state]
            self.match_index = state
        except IndexError:
            response = None
        return response

    def input_loop(self):
        line = self.default
        go_on = True
        while go_on:
            line = (raw_input('%s ("q" to quit, tab for options): ' % self.parsername) + (line and '(%s)' % line or ''))
            if line:
                line = line.strip()
            if line == 'q':
                return
            if line in self.options:
                go_on = False
                return line
            if self.match_index:
                try:
                    response = self.matches[self.match_index]
                    go_on = False
                    return response
                except IndexError:
                    pass



# Prompt the user for text
#input_loop()
