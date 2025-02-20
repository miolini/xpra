#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2020-2021 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from xpra.os_util import POSIX, OSX
from xpra.platform import program_context
from xpra.platform.gui import force_focus
from xpra.gtk_common.gtk_util import add_close_accel, get_icon_pixbuf

import os
from datetime import datetime
from collections import deque

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Pango, GLib    #pylint: disable=wrong-import-position


def make_window():
    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    window.set_title("Window Focus")
    window.set_size_request(640, 200)
    window.set_position(Gtk.WindowPosition.CENTER)
    window.connect("delete_event", Gtk.main_quit)
    icon = get_icon_pixbuf("windows.png")
    if icon:
        window.set_icon(icon)
    vbox = Gtk.VBox()
    hbox = Gtk.HBox()
    def add_btn(label, cb):
        b = Gtk.Button(label=label)
        def bcb(*_args):
            cb()
        b.connect('clicked', bcb)
        hbox.add(b)
    def restack_above():
        window.get_window().restack(None, True)
    add_btn("Restack Above", restack_above)
    def restack_below():
        window.get_window().restack(None, False)
    add_btn("Restack Below", restack_below)
    def _raise():
        window.get_window().raise_()
    add_btn("Raise", _raise)
    def _lower():
        window.get_window().lower()
    add_btn("Lower", _lower)
    vbox.add(hbox)
    N = 8
    labels = []
    font = Pango.FontDescription("sans 12")
    for _ in range(N):
        l = Gtk.Label()
        l.modify_font(font)
        labels.append(l)
    for l in labels:
        al = Gtk.Alignment(xalign=0, yalign=0.5, xscale=0.0, yscale=0)
        al.add(l)
        vbox.add(al)
    window.add(vbox)
    window.show_all()
    text = deque(maxlen=N)
    def update(s):
        text.append("%s: %s" % (datetime.now(), s))
        for i, t in enumerate(text):
            labels[i].set_text(t)
    #self.selectX11FocusChange(self)
    def focus_in(_window, _event):
        update("focus-in-event")
    def focus_out(_window, _event):
        update("focus-out-event")
    def has_toplevel_focus(window, _event):
        update("has-toplevel-focus: %s" % window.has_toplevel_focus())
    window.connect("focus-in-event", focus_in)
    window.connect("focus-out-event", focus_out)
    window.connect("notify::has-toplevel-focus", has_toplevel_focus)
    if POSIX and not OSX:
        from xpra.gtk_common.error import xlog
        from xpra.x11.gtk_x11.gdk_display_source import init_gdk_display_source
        from xpra.x11.gtk_x11.gdk_bindings import init_x11_filter
        from xpra.x11.bindings.window_bindings import X11WindowBindings  #pylint: disable=no-name-in-module
        from xpra.os_util import is_Wayland
        if not is_Wayland():
            #x11 focus events:
            gdk_win = window.get_window()
            xid = gdk_win.get_xid()
            init_gdk_display_source()
            os.environ["XPRA_X11_DEBUG_EVENTS"] = "FocusIn,FocusOut"
            init_x11_filter()
            with xlog:
                X11WindowBindings().selectFocusChange(xid)
    return window

def main():
    with program_context("window-focus", "Window Focus"):
        w = make_window()
        add_close_accel(w, Gtk.main_quit)
        from xpra.gtk_common.gobject_compat import register_os_signals
        def signal_handler(*_args):
            Gtk.main_quit()
        register_os_signals(signal_handler)
        def show_with_focus():
            force_focus()
            w.show_all()
            w.present()
        GLib.idle_add(show_with_focus)
        Gtk.main()
        return 0

if __name__ == "__main__":
    main()
