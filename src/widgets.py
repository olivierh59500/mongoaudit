# -*- coding: utf-8 -*-

import urwid

from testers import Tester

DIV = urwid.Divider()
HR = urwid.AttrMap(urwid.Divider('_'), 'hr')


def pad(widget, left=2, right=2):
    return urwid.Padding(widget, left=left, right=right)


class TextButton(urwid.Button):
    """
    Args:
      label (str): label for the text button
      on_press (function): callback
      user_data(): user_data for on_press
      align (str): (default right)
    """

    def __init__(self, label, on_press=None, user_data=None, align='right'):
        super(TextButton, self).__init__(
            label, on_press=on_press, user_data=user_data)
        self._label.align = align
        cols = urwid.Columns([self._label])
        super(urwid.Button, self).__init__(cols)


class Card(urwid.WidgetWrap):
    """
    Args:
      content (urwid.Widget):
      header (urwid.Widget):
      footer (urwid.Widget):
    """

    def __init__(self, content, header=None, footer=None):
        wlist = []
        if header:
            wlist.append(header)
        wlist.extend([DIV, pad(content)])
        if footer:
            wlist.extend([HR, DIV, pad(footer)])
        wlist.append(DIV)
        card = urwid.AttrMap(urwid.Pile(wlist), 'card')
        urwid.WidgetWrap.__init__(self, card)


class ObjectButton(urwid.Button):
    def __init__(self, content, on_press=None, user_data=None):
        self.__super.__init__('', on_press=on_press, user_data=user_data)

        super(urwid.Button, self).__init__(content)

    def get_content(self, text):
        return urwid.Pile([urwid.SelectableIcon(
            s, 0) if i == 0 else urwid.Text(s) for i, s in enumerate(text)])


class LineButton(ObjectButton):
    """
    Creates a LineBox button with an image on the left column and text on the right
    Args:
      text ((palette_class, str)[]): array of string tuples
    """

    def __init__(self, text, vertical_padding=True):
        content = self.get_content(text)

        content = [urwid.Padding(content, left=3, right=3)]
        if vertical_padding:
            content = [DIV] + content + [DIV]
        lbox = urwid.LineBox(urwid.Pile(content))
        self.__super.__init__(urwid.AttrMap(urwid.Pile(
            [lbox]), 'image button', 'image button focus'))


class ImageButton(ObjectButton):
    """
    Creates a LineBox button with an image on the left column and text on the right
    Args:
      pic (urwid.Pile): object created with picRead
      text ((palette_class, str)[]): array of string tuples
    """

    def __init__(self, pic, text):
        content = self.get_content(text)
        lbox = urwid.LineBox(urwid.Pile([DIV, urwid.Padding(
            urwid.Columns([(8, pic), content], 4), left=3, right=3), DIV]))
        self.__super.__init__(urwid.AttrMap(urwid.Pile(
            [lbox]), 'image button', 'image button focus'))


class InputField(urwid.WidgetWrap):
    """
    Creates an input field with underline and a label
    Args:
      label (str): label for the input
      label_width (int): label width (default 15 characters)
    """

    def __init__(self, label="", label_width=15, next=False):
        self.label, self.next = label, next
        self.edit = urwid.Padding(urwid.Edit(), left=1, right=1)
        label = urwid.LineBox(
            urwid.Text(label),
            tlcorner=' ',
            tline=' ',
            lline=' ',
            trcorner=' ',
            blcorner=' ',
            rline=' ',
            brcorner=' ',
            bline=' ')
        lbox = urwid.AttrMap(
            urwid.LineBox(
                self.edit,
                tlcorner=' ',
                tline=' ',
                lline=' ',
                trcorner=' ',
                blcorner=' ',
                rline=' ',
                brcorner=' '),
            'input',
            'input focus')
        cols = urwid.Columns([(label_width, label), lbox])
        urwid.WidgetWrap.__init__(self, cols)

    def get_text(self):
        """
        Returns:
          str: value of the input field
        """
        return self.edit.original_widget.get_text()[0]

    def get_label(self):
        """
        Returns:
          str: label for the input field
        """
        return self.label

    def keypress(self, size, key):
        if key is 'enter' and self.next:
            self.next()
        else:
            return self.__super.keypress(size, key)


class FormCard(urwid.WidgetWrap):
    """
    Args:
      content (urwid.Widget): any widget that can be piled
      field_labels (str[]): labels for the input_fields
      btn_label (str): label for the button
      cb (function): callback to invoke when the form button is pressed
      back (function): card to render when going back
    Note:
      cb must take the same amount of arguments as labels were passed and each parameter
      in the callback must be named as the label but in snake case and lower case e.g.
      'Field Name' =>  field_name
    """

    def __init__(self, content, field_labels, btn_label, cb, back=None):
        self.fields, self.cb = [], cb
        for label in field_labels:
            self.fields.append(InputField(label, next=self.next))
        input_fields = urwid.Pile(self.fields)
        self.error_field = urwid.Text('')
        error_row = urwid.Columns([(17, urwid.Text('')), self.error_field])
        buttons = [TextButton(btn_label, on_press=self.next)]
        if back:
            buttons.insert(0, TextButton('Back', align='left', on_press=back))
        footer = urwid.AttrMap(urwid.Columns(buttons), 'button')

        card = Card(urwid.Pile(
            [content, input_fields, error_row]), footer=footer)
        urwid.WidgetWrap.__init__(self, card)

    def next(self, _button=None):
        self.cb(form=self, **(self.get_field_values()))

    def get_field_values(self):
        """
        Returns:
          dict: the keys are the labels of the fields in snake_case
        """
        values = dict()
        for field in self.fields:
            values[field.get_label().lower().replace(" ", "_")] = field.get_text()

        return values

    def set_error(self, msg):
        """
        Args:
          msg (str): error message
        """
        self.error_field.set_text(('error', msg))


class TestRunner(urwid.WidgetWrap):
    """
    Run the test while displaying the progress

    Args:
      title (str): title to pass to the callback
      cred (dict(str: str)): credentials
      tests (Test[]): tests to run
      app (App):
      cb (function):  callback to call when the tests finish running
    """

    def __init__(self, title, cred, tests, app, cb):
        self.title = title
        self.cb = cb
        self.urn = cred["nodelist"][0][0] + ":" + str(cred["nodelist"][0][1]) + (
            "/" + (cred["database"]) if bool(cred["database"]) else "")
        self.number_of_test = len(tests)
        self.app = app

        self.tester = Tester(cred, tests)

        self.progress_text = urwid.Text(
            ('progress', '0/' + str(self.number_of_test)))
        running_display = urwid.Columns(
            [(14, urwid.Text(('text', 'Running check'))), self.progress_text])
        self.progress_bar = CustomProgressBar(
            'progress', 'remaining', 0, self.number_of_test)
        self.text_running = urwid.Text(('text', ''))
        box = urwid.BoxAdapter(urwid.Filler(
            self.text_running, valign='top'), 3)
        pile = urwid.Pile([DIV, running_display, self.progress_bar, DIV, box])
        urwid.WidgetWrap.__init__(self, pile)

    def each(self, test):
        """
        Update the description of the test currently running
        """
        current = self.progress_bar.get_current() + 1
        self.progress_text.set_text(
            ('progress', str(current) + '/' + str(self.number_of_test)))
        self.progress_bar.set_completion(current)
        self.text_running.set_text('Checking if ' + test.title + '...')
        self.app.loop.draw_screen()

    def run(self):
        """
        run tests
        """
        self.tester.run(self.each, self.end)

    def end(self, res):
        self.cb(res, self.title, self.urn)


class CustomProgressBar(urwid.ProgressBar):
    """
    ProgressBar that displays a semigraph instead of a percentage
    """
    semi = u'▁▂▃▄▅▆▇█'

    def get_text(self):
        """
        Return the progress bar percentage.
        """
        return min(100, max(0, int(self.current * 100 / self.done)))

    def get_current(self):
        """
        Return the current value of the ProgressBar
        """
        return self.current

    def get_done(self):
        """
        Return the end value of the ProgressBar
        """
        return self.done

    def render(self, size, focus=False):
        """
        Render the progress bar.
        """
        (maxcol,) = size
        cf = float(self.current) * maxcol / self.done
        ccol = int(cf)
        txt = urwid.Text([(self.normal, self.semi[1] * ccol),
                          (self.complete, self.semi[1] * (maxcol - ccol))])
        c = txt.render(size)

        return c


class DisplayTest(urwid.WidgetWrap):
    """
    Display test result
    """

    currently_displayed = 0
    top_columns = urwid.Columns([])
    test_result = urwid.Pile([])

    def __init__(self, result):
        self.result = result
        self.total = len(result)
        self.update_view('next')

        walker = urwid.SimpleListWalker([urwid.Padding(self.top_columns, left=3, right=3),
                                         self.test_result])

        adapter = urwid.BoxAdapter(urwid.ListBox(walker), height=16)

        urwid.WidgetWrap.__init__(self, adapter)

    def test_display(self, test, options):
        """
        Compose the element that will display the test
        Returns:
            [urwid.Widget]:
        """
        div_option = (DIV, options('weight', 1))
        title = (urwid.Text(
            ('text bold', test['title'])), options('weight', 1))
        caption = (urwid.Text(
            ('text', test['caption'])), options('weight', 1))
        severity = (urwid.Text(
            ('text', 'Severity: ' + ['High', 'Medium', 'Low'][test['severity']])),
                    options('weight', 1))
        result = (urwid.Text(
            [('text', 'Result: '), (['error', 'ok', 'warning', 'info'][test['result']],
                                    ' ' + ['✘', '✔', '!', '*'][test['result']]),
             ('text', [' failed', ' passed', ' warning', ' omitted'][test['result']])]),
                  options('weight', 1))


        if isinstance(test['message'], list):
            message_string = test['message'][0] + \
                             test['extra_data'] + test['message'][1]
        else:
            message_string = test['message']
        message = (urwid.Text(
            ('text', message_string)), options('weight', 1))
        return [div_option, title, div_option, caption, div_option, severity,
                result, div_option, message]

    def get_top_text(self):
        """
        Returns:
            tuple(str,str): palette , Test n/total
        """
        return 'header red', 'Test ' + \
               str(self.currently_displayed) + '/' + str(self.total)

    def get_top_row(self, current, options):

        def get_button(sign, text):
            return urwid.AttrMap(TextButton(sign, on_press=(
                lambda _: self.update_view(text))), 'button')

        next_btn = get_button('>', 'next')
        prev_btn = get_button('<', 'prev')
        top_row = []
        if current > 1:
            top_row.append((prev_btn, options('weight', 0)))
        top_row.append((urwid.Padding(urwid.Text(self.get_top_text()),
                                      left=25), options('weight', 1)))
        if current < len(self.result):
            top_row.append((next_btn, options('weight', 0.2)))
        return top_row

    def update_currently_displayed(self, btn):
        self.currently_displayed += 1 if btn is 'next' else -1

    def set_focus_position(self, current, btn):
        focus = 0  # moving to the left
        if current <= 1:
            focus = 1  # first element
        elif btn is 'next' and current < self.total:
            focus = 2  # moving to the right
        self.top_columns.focus_position = focus

    def update_view(self, btn):
        self.update_currently_displayed(btn)
        self.top_columns.contents = self.get_top_row(
            self.currently_displayed, self.top_columns.options)

        self.set_focus_position(self.currently_displayed, btn)
        self.test_result.contents = self.test_display(
            self.result[self.currently_displayed - 1], self.test_result.options)
