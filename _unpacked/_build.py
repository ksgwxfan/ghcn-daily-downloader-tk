import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog as tksimp
import re
import os
import gzip
import json
import functools
import collections
import sqlite3
import tempfile
import webbrowser
import _countries

class Build:

    def build_stations(self):
        """Formulate the stations dictionary from the GHCNDaily database."""
        Station = collections.namedtuple(
            "Station",
            [
                "id", "latitude", "longitude", "elevation", "state", "name",
                "gsn", "hcn_crn", "wmo_id", "country", "size",
                "prcp_start", "prcp_end",
                "snow_start", "snow_end",
                "snwd_start", "snwd_end",
                "tmax_start", "tmax_end",
                "tmin_start", "tmin_end",
                "is_available"
            ]
        )

        try:
            with gzip.open("GHCNDaily.db.gz") as r:
                self.stations_db = tempfile.NamedTemporaryFile(delete=False)
                self.stations_db.write(gzip.decompress(r.read()))
                _stndb = sqlite3.connect(self.stations_db.name)
                self.stations = {
                    row[0] : Station(*row) for row in _stndb.execute("SELECT * FROM GHCNDaily")
                }
                _stndb.close()
        except FileNotFoundError:
            print(
                "* The file 'GHCNDaily.db.gz' was not found. This file "
                "contains a database neccessary for the function of the "
                "program. Please go to "
                "'https://ksgwxfan.github.com/ghcn-daily-downloader-tk/' to "
                "download it and place it in the same directory as the app "
                "you are running."
            )
            raise

    def build_menu(self):
        """Compile menu commands for convience."""
        self.toolbar = tk.Menu(self.window)
        self.window["menu"] = self.toolbar

        # File
        file = tk.Menu(self.toolbar, tearoff=0)
        self.toolbar.add_cascade(label="File", menu=file)
        file.add_command(
            label="Close",
            command=self.window.destroy
        )

        # Options
        optmenu = tk.Menu(self.toolbar, tearoff=0)
        self.toolbar.add_cascade(label="Options", menu=optmenu)

        # Results sorting
        sort_method_menu = tk.Menu(optmenu, tearoff=0)
        optmenu.add_cascade(label="Sort Results By", menu=sort_method_menu)
        sort_method_menu.add_radiobutton(
            label = "Station ID (also Country Abbreviation)",
            variable = self.sort_method,
            value = "id",
            command = functools.partial(
                self.resort_results,
                True
            )
        )
        sort_method_menu.add_radiobutton(
            label = "Station Name / Description",
            variable = self.sort_method,
            value = "name",
            command = functools.partial(
                self.resort_results,
                True
            )
        )
        sort_method_menu.add_radiobutton(
            label = "State",
            variable = self.sort_method,
            value = "state",
            command = functools.partial(
                self.resort_results,
                True
            )
        )
        sort_method_menu.add_radiobutton(
            label = "Latitude",
            variable = self.sort_method,
            value = "latitude",
            command = functools.partial(
                self.resort_results,
                True
            )
        )
        sort_method_menu.add_radiobutton(
            label = "Longitude",
            variable = self.sort_method,
            value = "longitude",
            command = functools.partial(
                self.resort_results,
                True
            )
        )
        sort_method_menu.add_radiobutton(
            label = "Elevation",
            variable = self.sort_method,
            value = "elevation",
            command = functools.partial(
                self.resort_results,
                True
            )
        )
        sort_method_menu.add_radiobutton(
            label = "File-Size",
            variable = self.sort_method,
            value = "size",
            command = functools.partial(
                self.resort_results,
                True
            )
        )

        # Results sorting direction
        optmenu.add_separator()
        optmenu.add_radiobutton(
            label="Ascending (A-Z; low-to-high)",
            variable = self.sort_direction,
            value = 0,
            command = functools.partial(
                self.resort_results,
                True
            )
        )
        optmenu.add_radiobutton(
            label="Descending (Z-A; high-to-low)",
            variable = self.sort_direction,
            value = 1,
            command = functools.partial(
                self.resort_results,
                True
            )
        )

        # Overwrite option
        optmenu.add_separator()
        optmenu.add_checkbutton(
            label = "Overwrite existing GHCN-Daily Archives",
            offvalue = False,
            onvalue = True,
            variable = self.overwrite,
            command = self.save_defaults
        )

        # Help
        helpmenu = tk.Menu(self.toolbar, tearoff=0)
        helpmenu.add_command(
            label="Quick Tips",
            command=functools.partial(
                QuickTips,
                self.window,
                "Quick Tips"
            )
        )
        self.toolbar.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(
            label = "Country Codes",
            command = functools.partial(
                CountryCodes,
                self.window,
                "Country Codes",
                "countries"
            )
        )
        helpmenu.add_command(
            label = "State (Province) Codes",
            command = functools.partial(
                CountryCodes,
                self.window,
                "State Codes",
                "states"
            )
        )
        helpmenu.add_separator()
        helpmenu.add_command(
            label="About",
            command=functools.partial(
                About,
                self.window,
                "About GHCN-Daily Downloader Tk"
            )
        )

    def build_app(self):
        """Formulate the Structure of the app."""

        # Query Framework
        self.search_frame = tk.LabelFrame(
            self.window,
            text = "Build Query"
        )
        self.search_frame.pack(fill=tk.X, padx=10, pady=5, ipady=2)

        # DESCRIPTION/NAME ENTRY
        def entry_validation(en):
            self.query_ready(self.entry, en)
            return True

        self.entry_frame = tk.Frame(
            self.search_frame,
        )
        self.entry_frame.pack(fill=tk.X)

        lbl = tk.Label(
            self.entry_frame,
            text = "Description: ",
        )
        lbl.pack(side=tk.LEFT)

        entry_ok = self.window.register(entry_validation)
        self.entry = tk.Entry(
            self.entry_frame,
            validate = "key",
            validatecommand = (entry_ok, "%P")
        )
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # STATE / COUNTRY
        self.state_frame = tk.Frame(
            self.search_frame
        )
        self.state_frame.pack(fill=tk.X)

        lbl = tk.Label(
            self.state_frame,
            text = "State/Country Filter: ",
        )
        lbl.pack(side=tk.LEFT)

        def make_state_uppercase(event):
            """Aesthetics function to make country/state abbreviations upper-
            case."""
            txt = self.filter_state.get()
            if len(self.filter_state.get()) > 0 \
            and self.filter_state.get().isupper() is False:
                self.filter_state.delete(0, tk.END)
                self.filter_state.insert(tk.END, txt.upper())

        def state_validation(st):
            """Returns a bool whether or not the State abbreviation is valid."""
            self.query_ready(self.filter_state, st)
            if bool(re.search(r"[^A-Z]", st, flags=re.I)) or len(st) > 2:
                return False
            else:
                return True

        state_ok = self.window.register(state_validation)

        self.filter_state = tk.Entry(
            self.state_frame,
            validate = "key",
            font = (None, 14, "bold"),
            justify = tk.CENTER,
            validatecommand = (state_ok, "%P"),
            width = 5,
        )
        self.filter_state.pack(side=tk.LEFT)
        self.filter_state.bind(
            "<Any-KeyRelease>",
            make_state_uppercase
        )

        # COORDINATES; LAT LON

        def toggle_2nd_coords():
            """Manages the display of the 2nd-set of coordinates."""
            # OFF
            if self.coord_boundingbox_toggle.get() == 0:
                self.lat_entry2["state"] = tk.DISABLED
                self.lon_entry2["state"] = tk.DISABLED
                self.lat_entry2["foreground"] = "gray"
                self.lon_entry2["foreground"] = "gray"
                self.lat_entry2["cursor"] = "arrow"
                self.lon_entry2["cursor"] = "arrow"
                self.lat_logic_select.pack(side=tk.LEFT, before=self.lat_entry1)
                self.lon_logic_select.pack(side=tk.LEFT, before=self.lon_entry1)
                # This is to simply enable/disable submit button
                self.query_ready(
                    self.lat_entry1,
                    self.lat_entry1.get()
                )
            # ON
            else:
                self.lat_entry2["state"] = tk.NORMAL
                self.lon_entry2["state"] = tk.NORMAL
                self.lat_entry2["foreground"] = "SystemWindowText"
                self.lon_entry2["foreground"] = "SystemWindowText"
                self.lat_entry2["cursor"] = "xterm"
                self.lon_entry2["cursor"] = "xterm"
                self.lat_logic_select.pack_forget()
                self.lon_logic_select.pack_forget()
                # This is to simply enable/disable submit button
                self.query_ready(
                    self.lat_entry1,
                    self.lat_entry1.get()
                )

        self.coordinates_frame = tk.LabelFrame(
            self.search_frame,
            text = "Coordinates",
        )
        self.coordinates_frame.pack(fill=tk.X, padx=5)
        # bouding-box toggle
        self.coord_boundingbox_toggle = tk.IntVar()
        self.coord_boundingbox = tk.Checkbutton(
            self.coordinates_frame,
            text = "Coordinate Bounding Box?",
            variable = self.coord_boundingbox_toggle,
            command = toggle_2nd_coords
        )
        self.coord_boundingbox.pack()

        def latitude_validation(lat, _widget):
            """Ensures a entered latitude is valid; primarily that the number
            entered is between -90 and 90.
            """
            try:
                if len(lat) == 0 \
                or (len(lat) == 1 and bool(re.search(r"^[\d\-]", lat))) \
                or -90 <= int(lat) <= 90:
                    self.query_ready(
                        self.window.nametowidget(_widget),
                        lat
                    )
                    return True
                else:
                    return False
            except ValueError:
                return False

        lat_ok = self.window.register(latitude_validation)

        def longitude_validation(lon, _widget):
            """Ensures a entered longitude is valid; primarily that the number
            entered is -180 < LONGITUDE < 180.
            """
            try:
                if len(lon) == 0 \
                or (len(lon) == 1 and bool(re.search(r"^[\d\-]", lon))) \
                or -180 < int(lon) < 180:
                    self.query_ready(
                        self.window.nametowidget(_widget),
                        lon
                    )
                    return True
                else:
                    return False
            except ValueError:
                return False

        lon_ok = self.window.register(longitude_validation)

        # coord1
        coord1_frame = tk.Frame(self.coordinates_frame)
        coord1_frame.pack()

        lbl = tk.Label(coord1_frame, text = "Lat1: ")
        lbl.pack(side=tk.LEFT)

        self.lat_logic = tk.StringVar(value = ">=")
        self.lat_logic_select = tk.OptionMenu(
            coord1_frame,
            self.lat_logic,
            ">=",
            "<=",
        )
        self.lat_logic_select.pack(side=tk.LEFT)

        self.lat_entry1 = tk.Entry(
            coord1_frame,
            validate = "key",
            font = (None, 14, "bold"),
            justify = tk.CENTER,
            validatecommand = (lat_ok, "%P", "%W"),
            width = 5,
        )
        self.lat_entry1.pack(side=tk.LEFT)

        lbl = tk.Label(coord1_frame, text = "Lon1: ")
        lbl.pack(side=tk.LEFT)

        self.lon_logic = tk.StringVar(value = "<=")
        self.lon_logic_select = tk.OptionMenu(
            coord1_frame,
            self.lon_logic,
            "<=",
            ">=",
        )
        self.lon_logic_select.pack(side=tk.LEFT)

        self.lon_entry1 = tk.Entry(
            coord1_frame,
            validate = "key",
            font = (None, 14, "bold"),
            justify = tk.CENTER,
            validatecommand = (lon_ok, "%P", "%W"),
            width = 5,
        )
        self.lon_entry1.pack(side=tk.LEFT)

        # coord2
        coord2_frame = tk.Frame(self.coordinates_frame)
        coord2_frame.pack()

        lbl = tk.Label(coord2_frame, text = "Lat2: ")
        lbl.pack(side=tk.LEFT)

        self.lat_entry2 = tk.Entry(
            coord2_frame,
            validate = "key",
            font = (None, 14, "bold"),
            justify = tk.CENTER,
            state = tk.DISABLED,
            validatecommand = (lat_ok, "%P", "%W"),
            cursor = "arrow",
            width = 5,
        )
        self.lat_entry2.pack(side=tk.LEFT)

        lbl = tk.Label(coord2_frame, text = "Lon2: ")
        lbl.pack(side=tk.LEFT, anchor=tk.CENTER, expand=True)

        self.lon_entry2 = tk.Entry(
            coord2_frame,
            validate = "key",
            font = (None, 14, "bold"),
            justify = tk.CENTER,
            state = tk.DISABLED,
            validatecommand = (lon_ok, "%P", "%W"),
            cursor = "arrow",
            width = 5,
        )
        self.lon_entry2.pack(side=tk.LEFT)

        # ELEVATION
        self.elev_frame = tk.Frame(
            self.search_frame
        )
        self.elev_frame.pack(fill=tk.X)
        lbl = tk.Label(
            self.elev_frame,
            text = "Elevation (m): ",
        )
        lbl.pack(side=tk.LEFT)

        def elev_validation(elev):
            """Returns a bool indicating if an entered elevation is valid."""
            self.query_ready(self.filter_elevation, elev)
            return bool(
                re.search(
                    r"^$|^[\-0-9]{1}$|^[\-0-9]{1}[0-9]+$",
                    elev
                )
            )

        self.elev_logic = tk.StringVar(value = "<=")
        self.elev_logic_select = tk.OptionMenu(
            self.elev_frame,
            self.elev_logic,
            "<=",
            ">=",
        )
        self.elev_logic_select.pack(side=tk.LEFT)
        self.elev_logic_select.bind(
            "<KeyRelease-Escape>",
            self.elev_logic_select.grab_release
        )

        elev_ok = self.window.register(elev_validation)
        self.filter_elevation = tk.Entry(
            self.elev_frame,
            font = (None, 12, "bold"),
            justify = tk.CENTER,
            validate = "key",
            validatecommand = (elev_ok, "%P"),
            width = 8,
        )
        self.filter_elevation.pack(side=tk.LEFT)

        btnfrm = tk.Frame(
            self.search_frame,
        )
        btnfrm.pack(expand=True, fill=tk.X, anchor=tk.W)
        # Clear Query Button
        clr_query_btn = tk.Button(
            btnfrm,
            text="Clear Query",
            command = self.query_clear
        )
        clr_query_btn.pack(side = tk.LEFT)
        # search button
        self.entry_btn = tk.Button(
            btnfrm,
            text="Submit Query",
            font=(None, 12, "bold"),
            state=tk.DISABLED,
            command=self.search
        )
        self.entry_btn.pack(side=tk.LEFT, padx=30, ipadx=20)

        self.window.bind_all(
            "<KeyRelease-Return>",
            self.search_ready
        )

        self.results_label = tk.Label(
            self.search_frame,
            font = (None, 9, "normal"),
            foreground = "blue",
        )
        self.results_label.pack(fill=tk.X)

        #Results
        self.box_results = tk.Listbox(
            self.window,
            font = ("Courier", 9, ""),
            exportselection = 0,
            selectmode = tk.SINGLE,
        )
        self.box_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.box_results.bind(
            "<ButtonRelease-1>",
            self.verify_selection
        )
        results_scroll = tk.Scrollbar(
            self.box_results,
            orient=tk.VERTICAL,
            command=self.box_results.yview
        )
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.box_results["yscrollcommand"] = results_scroll.set

        # Download Frame
        self.download_frame = tk.Frame(self.window)
        self.download_frame.pack(padx=10, pady=10, fill=tk.X)

        self.station_info_btn = tk.Button(
            self.download_frame,
            text = "View Station Info",
            state = tk.DISABLED,
            command = self.display_station_info
        )
        self.station_info_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.download_btn = tk.Button(
            self.download_frame,
            text = "Download",
            state = tk.DISABLED,
            command = self.download
        )
        self.download_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def display_station_info(self):
        stn = self.results[
            self.box_results.curselection()[0]
        ]
        StationInfo(
            self.window,
            "{} - {}".format(stn.id, stn.name),
            stn
        )

class CountryCodes(tksimp.Dialog):
    def __init__(self, parent, title=None, what="countries"):
        self.what = what
        super().__init__(parent, title)

    def buttonbox(self):
        btn = tk.Button(
            self,
            width = 10,
            text = "OK",
            default = tk.ACTIVE,
            command = self.cancel
        )
        btn.pack(side=tk.RIGHT, padx=15, pady=5)
        btn.focus_set()
        self.bind("<KeyRelease-Return>", self.cancel)
        self.bind("<KeyRelease-space>", self.cancel)
        self.bind("<Escape>", self.cancel)

    def body(self, master):
        self.winfo_toplevel().resizable(False, False)
        # master.pack_propagate(0)
        # master["width"] = 350
        # master["height"] = 460
        # master.pack(fill=tk.BOTH, expand=True)
        # master.pack_propagate(1)

        msg = tk.Label(
            master,
            text = "Here is a list of {}{} found in the GHCNDaily Database:".format(
                self.what,
                " (Mostly in the USA\nand Canada)" if self.what == "states" else ""
            )
        )
        msg.pack()

        list_frame = tk.Frame(master)
        list_frame.pack(expand=True, fill=tk.BOTH)

        info = tk.Text(
            list_frame,
            font = ("Courier", 9, ""),
            relief = tk.SUNKEN,
            width = 50,
            wrap = tk.NONE,
        )
        # Countries
        if self.what == "countries":
            info.insert(
                tk.END,
                "\n".join([
                    "{} - {}".format(abbr, name)
                    for abbr, name in _countries.dictionary.items()
                ])
            )
        # States
        else:
            info.insert(
                tk.END,
                "\n".join([
                    "{} - {}".format(abbr, name)
                    for abbr, name in _countries.states.items()
                ])
            )
        info["state"] = tk.DISABLED
        # info.pack(expand=True, fill=tk.BOTH)
        info.grid(
            row=0,
            column=0,
            sticky=tk.N+tk.S+tk.E+tk.W,
        )
        
        info_scroll = tk.Scrollbar(
            list_frame,
            orient = tk.VERTICAL,
            command = info.yview,
            cursor = "arrow",
        )
        # info_scroll.pack(
            # side=tk.RIGHT,
            # fill=tk.Y
        # )
        info_scroll.grid(
            row=0,
            column=1,
            sticky=tk.N+tk.S+tk.E,
        )

        info["yscrollcommand"] = info_scroll.set

class StationInfo(tksimp.Dialog):
    def __init__(self, parent, title=None, stnobj=None):
        self.station_id = stnobj.id
        self.station_obj = stnobj
        super().__init__(parent, title)

    def buttonbox(self):
        self.winfo_toplevel().resizable(False, False)
        btn = tk.Button(
            self,
            width = 10,
            text = "OK",
            default = tk.ACTIVE,
            command = self.cancel
        )
        btn.pack(side=tk.RIGHT, padx=15, pady=5)
        btn.focus_set()
        self.bind("<KeyRelease-Return>", self.cancel)
        self.bind("<KeyRelease-space>", self.cancel)
        # self.bind("<Escape>", self.cancel)

    def body(self, master):
        info = tk.Text(
            master,
            width = 40,
            background = "SystemButtonFace",
        )
        for line in [
            "ID: {}".format(self.station_obj.id),
            "Name: {}".format(self.station_obj.name),
            "Country: {} ({})".format(
                self.station_obj.country,
                _countries.dictionary[
                    self.station_obj.country
                ]
            ),
            "{}{}".format(
                "State: {} ({})\n".format(
                    self.station_obj.state,
                    _countries.states[self.station_obj.state]
                ),
                "Latitude: {}".format(self.station_obj.latitude)
            ),
            "Longitude: {}".format(self.station_obj.longitude),
            "Elevation: {}".format(
                "{}m ({}ft)".format(
                    self.station_obj.elevation,
                    round(self.station_obj.elevation * 3.28, 1)
                ) if self.station_obj.elevation > -999 else "N/A"
            ),
            # ["ACW00011604", 17.1167, -61.7833, 10.1, null, "ST JOHNS COOLIDGE FLD", false, false, null, "AC", 3.9, 1949, 1949, 1949, 1949, 1949, 1949, 1949, 1949, 1949, 1949, true]
            # "gsn", "hcn_crn", "wmo_id"
            "\n".join([
                "",
                "GCOS Surface Network?: {}".format(
                    "Y" if self.station_obj.gsn is True else "N"
                ),
                "HCN/CRN Network?: {}".format(
                    "Y" if self.station_obj.hcn_crn is True else "N"
                ),
                "WMO Id: {}".format(self.station_obj.wmo_id),
                ""
            ]),
            "Size (in KB): {}".format(self.station_obj.size),
            "",
            "Data-Ranges",
            "-----------",
            "PRCP: {}-{}".format(
                self.station_obj.prcp_start,
                self.station_obj.prcp_end,
            ),
            "SNOW: {}-{}".format(
                self.station_obj.snow_start,
                self.station_obj.snow_end,
            ),
            "SNWD: {}-{}".format(
                self.station_obj.snwd_start,
                self.station_obj.snwd_end,
            ),
            "TMAX: {}-{}".format(
                self.station_obj.tmax_start,
                self.station_obj.tmax_end,
            ),
            "TMIN: {}-{}".format(
                self.station_obj.tmin_start,
                self.station_obj.tmin_end,
            ),
        ]:
            info.insert(tk.END, line + "\n")
        info["state"] = tk.DISABLED
        info.pack()

class QuickTips(tksimp.Dialog):
    def __init__(self, parent, title=None):
        super().__init__(parent, title)

    def buttonbox(self):
        self.winfo_toplevel().resizable(False, False)
        sep = ttk.Separator(self, orient = tk.HORIZONTAL)
        sep.pack(fill=tk.X)
        btn = tk.Button(
            self,
            width = 10,
            text = "OK",
            command = self.ok
        )
        btn.pack(side=tk.RIGHT, padx=15, pady=5)
        self.bind("<KeyRelease-Return>", self.ok)
        self.bind("<KeyRelease-space>", self.cancel)
        # self.bind("<Escape>", self.cancel)

    def body(self, master):
        lbl = tk.Message(
            master,
            text = "\n\n".join([
                "* Consult the Country and State codes in the help menu to "
                "properly interpret and determine desired abbreviation for the " "country/state filter",
                "* Regular Expressions are acceptable in the Description "
                "entry. Queries are also case-insensitive.",
                "* If searching for data from airport stations, using this "
                "regular expression will narrow the search: \n"
                "         airport|\\bAP\\b|\\bINTL\\b",
                "* Keyboard shortcuts:\n{}".format(
                    "\n".join([
                        "    - 'Enter' or 'Return' - attempts to submit and run the query."
                    ])
                )
            ]),
            aspect = 250,
        )
        lbl.pack(fill=tk.BOTH)

class About(tksimp.Dialog):
    def __init__(self, parent, title=None):
        super().__init__(parent, title)

    def open_addr(self, address, event=None):
        webbrowser.open_new_tab(address)

    def buttonbox(self):
        self.winfo_toplevel().resizable(False, False)
        btn = tk.Button(
            self,
            width = 10,
            text = "OK",
            command = self.ok
        )
        btn.pack(side=tk.RIGHT, padx=15, pady=5)
        self.bind("<KeyRelease-Return>", self.ok)
        self.bind("<KeyRelease-space>", self.cancel)
        # self.bind("<Escape>", self.cancel)

    def body(self, master):

        for txt, _tkwidget, href, cnf, add_sep in [
            ("GHCN-Daily Downloader Tk, v1.0", tk.Label, None, None, False),
            ("\u00a9 2022, Kyle S. Gentry", tk.Label, None, None, True),
            (
                "https://ksgwxfan.github.com/ghcnd-downloader-tk",
                tk.Label,
                "https://ksgwxfan.github.com/ghcnd-downloader-tk",
                None,
                False
            ),
            (
                "https://ksgwxfan.github.io",
                tk.Label,
                "https://ksgwxfan.github.io",
                None,
                False
            ),
            (
                "KyleSGentry@outlook.com",
                tk.Label,
                "mailto:kylesgentry@outlook.com",
                None,
                True
            ),
            (
                " ".join([
                    "This python tkinter zipapp expedites the retrieval of",
                    "weather-station data in gzip format for over 118,000",
                    "stations on the 'Daily Global Historical Climatology",
                    "Network'.",
                    "\n\n"
                ]) + " ".join([
                    "It enables running queries on the database based on a",
                    "number of filters. The search results can then be sorted",
                    "according to preference via the Options menu and",
                    "information for individual stations can be quickly",
                    "summoned and inspected prior to downloading."
                ]),
                tk.Message,
                None,
                {"aspect": 400},
                True
            ),
            (
                "Source for the Data:\n" \
                    + "  NOAA National Climatic Data Center. Global " \
                    + "Historical Climatology Network - Daily (GHCN-Daily). " \
                    + "Version 3.x",
                tk.Message,
                None,
                {"aspect": 700},
                False
            ),
            (
                "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/",
                tk.Label,
                "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/",
                None,
                False
            ),
        ]:
            lbl = _tkwidget(
                master,
                borderwidth=0,
                anchor = tk.W,
                justify = tk.LEFT,
                text = txt,
            )
            if cnf is not None:
                for attr, valu in cnf.items():
                    lbl[attr] = valu
            if href is not None:
                lbl["fg"] = "blue"
                lbl["font"] = (None, 9, "underline")
                lbl["cursor"] = "hand2"
                lbl.bind(
                    "<ButtonRelease-1>",
                    functools.partial(
                        self.open_addr,
                        href,
                    )
                )
            lbl.pack(
                expand=True,
                anchor=None if href is None else tk.W,
                fill=tk.X if href is None else None,
                padx=10 if href is not None else 0
            )

            if add_sep is True:
                sep = ttk.Separator(master)
                sep.pack(fill=tk.X, expand=True, pady=5)
















