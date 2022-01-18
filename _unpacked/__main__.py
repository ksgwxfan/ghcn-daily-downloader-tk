import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox as tkmsg
import re
import os
import operator
import sqlite3
import configparser
import urllib.request
import urllib.error
import datetime
import pprint
import _build
import _countries

class GHCNDailyFinder(_build.Build):
    def __init__(self):
        self.window = tk.Tk()
        self.config = configparser.ConfigParser()
        self.window.minsize(380, 500)
        self.window.resizable(False, False)
        self.window.title("GHCN-Daily Downloader Tk")
        self.results = []

        if os.path.exists("ghcnd.ini") is False:
            # This implies that it is the user's first time running the program...
            self.window.withdraw()
            answer = tkmsg.askyesno(
                title="Notice to User",
                message= "This program needs access to your temporary files "
                    "(only while the program is running) to give a physical "
                    "location to a required database."
                    "\n\n"
                    "If you agree to this requirement, please click 'Yes'. "
                    "Otherwise, the program will close."
            )
            if answer is True:
                self.window.deiconify()
            else:
                self.window.destroy()
                return None

        self.load_defaults()

        self.build_stations()
        self.window.bind(
            "<Destroy>",
            self.del_tempfile_database
        )

        self.build_menu()
        self.build_app()

        self.window.mainloop()

    def del_tempfile_database(self, event=None):
        """Upon closing the tkinter app (via menu or app 'x' button), this
        method ensures the deletion of the temporary database used by the
        program.
        """
        self.stations_db.close()
        try:
            os.remove(self.stations_db.name)
        except:
            pass

    def load_defaults(self):
        """While initializing the program, this method checks for and, if
        necessary, creates a file, 'ghcnd.ini': a file containing default
        options; remembering them (saving upon any change made) for subsequent
        uses of the program. 
        """
        try:
            with open("ghcnd.ini") as r:
                self.config.read_string(r.read())
        except:
            print("* No default settings file named 'ghcnd.ini' found. Creating...")
            self.config["DEFAULT"] = {
                "sortmethod" : "id",
                "descending" : 0,
                "overwrite" : "true"
            }
            with open("ghcnd.ini", "w") as w:
                self.config.write(w)

        self.sort_method = tk.StringVar(
            value=self.config["DEFAULT"]["sortmethod"]
        )
        self.sort_direction = tk.IntVar(
            value=self.config.getint(
                "DEFAULT",
                "descending"
            )
        )
        self.overwrite = tk.BooleanVar(
            value=self.config.getboolean("DEFAULT", "overwrite")
        )

    def save_defaults(self):
        """Saves the current settings from the option menu for subsequent use
        of the program. This method is called every time one of the options
        from the menu is altered.
        """
        self.config["DEFAULT"]["sortmethod"] = self.sort_method.get()
        self.config["DEFAULT"]["descending"] = str(self.sort_direction.get())
        self.config["DEFAULT"]["overwrite"] = str(self.overwrite.get()).lower()

        with open("ghcnd.ini", "w") as w:
            self.config.write(w)

    def query_clear(self):
        """Clears each entry widget in the program."""
        self.entry.delete(0, tk.END)
        self.filter_state.delete(0, tk.END)
        self.lat_entry1.delete(0, tk.END)
        self.lon_entry1.delete(0, tk.END)
        self.lat_entry2.delete(0, tk.END)
        self.lon_entry2.delete(0, tk.END)
        self.filter_elevation.delete(0, tk.END)
        self.query_ready(self.entry, "")

    def query_ready(self, widget, change, event=None):
        """This method determines when the 'Submit Query' button can be pressed
        by the user.
        """
        # print("'{}'".format(widget), "'{}'".format(change), len(change))
        if (
            widget == self.entry and (
                len(change) > 0 or \
                len(self.filter_state.get()) == 2 or \
                (
                    len(self.filter_elevation.get()) > 0 and \
                    self.filter_elevation.get() != "-"
                ) or (
                    self.coord_boundingbox_toggle.get() == 0 and \
                    any(len(w.get()) > 0 for w in [
                        self.lat_entry1, self.lon_entry1
                    ])
                ) or \
                (
                    self.coord_boundingbox_toggle.get() == 1 and \
                    all(len(w.get()) > 0 for w in [
                        self.lat_entry1,
                        self.lon_entry1,
                        self.lat_entry2,
                        self.lon_entry2,
                    ])
                )
            )
        ) or (
            widget == self.filter_state and (
                len(change) in [0,2] and \
                (
                    len(change) == 2 or \
                    len(self.entry.get()) > 0 or \
                    (
                        len(self.filter_elevation.get()) > 0 and \
                        self.filter_elevation.get() != "-"
                    ) or (
                        self.coord_boundingbox_toggle.get() == 0 and \
                        any(len(w.get()) > 0 for w in [
                            self.lat_entry1, self.lon_entry1
                        ])
                    ) or \
                    (
                        self.coord_boundingbox_toggle.get() == 1 and \
                        all(len(w.get()) > 0 for w in [
                            self.lat_entry1,
                            self.lon_entry1,
                            self.lat_entry2,
                            self.lon_entry2,
                        ])
                    )
                )
            )
        ) or (
            widget in [
                    self.lat_entry1, self.lon_entry1,
                    self.lat_entry2, self.lon_entry2
            ] and (
                len(self.entry.get()) > 0 or \
                len(self.filter_state.get()) == 2 or \
                (
                    len(self.filter_elevation.get()) > 0 and \
                    self.filter_elevation.get() != "-"
                ) or (
                    self.coord_boundingbox_toggle.get() == 0 and \
                    ((len(change) > 0 and change != "-") or \
                    any([
                        widget == self.lat_entry1 and (
                            len(self.lon_entry1.get()) > 0 and \
                            self.lon_entry1.get() != "-"
                        ),
                        widget == self.lon_entry1 and (
                            len(self.lat_entry1.get()) > 0 and \
                            self.lat_entry1.get() != "-"
                        ),
                    ])
                )) or (
                    self.coord_boundingbox_toggle.get() == 1 and \
                    (
                        (widget == self.lat_entry1 and (
                                len(change) > 0 and change != "-"
                        ) and all(
                            len(w.get()) > 0 and w.get() != "-" for w in [
                                self.lat_entry2,
                                self.lon_entry1,
                                self.lon_entry2,
                            ]
                        )) or \
                        (widget == self.lat_entry2 and (
                                len(change) > 0 and change != "-"
                        ) and all(
                            len(w.get()) > 0 and w.get() != "-" for w in [
                                self.lat_entry1,
                                self.lon_entry1,
                                self.lon_entry2,
                            ]
                        )) or \
                        (widget == self.lon_entry1 and (
                                len(change) > 0 and change != "-"
                        ) and all(
                            len(w.get()) > 0 and w.get() != "-" for w in [
                                self.lat_entry1,
                                self.lat_entry2,
                                self.lon_entry2,
                            ]
                        )) or \
                        (widget == self.lon_entry2 and (
                                len(change) > 0 and change != "-"
                        ) and all(
                            len(w.get()) > 0 and w.get() != "-" for w in [
                                self.lat_entry1,
                                self.lat_entry2,
                                self.lon_entry1,
                            ]
                        ))
                    )
                )
            )
        ) or (
            widget == self.filter_elevation and (
                (len(change) > 0 and change != "-") or \
                len(self.entry.get()) > 0 or \
                len(self.filter_state.get()) == 2 or \
                (
                    self.coord_boundingbox_toggle.get() == 0 and \
                    any(len(w.get()) > 0 for w in [
                        self.lat_entry1, self.lon_entry1
                    ])
                ) or \
                (
                    self.coord_boundingbox_toggle.get() == 1 and \
                    all(len(w.get()) > 0 for w in [
                        self.lat_entry1,
                        self.lon_entry1,
                        self.lat_entry2,
                        self.lon_entry2,
                    ])
                )
            )
        ):
            self.entry_btn["state"] = tk.NORMAL
            # reset incomplete entries

            return True
        else:
            self.entry_btn["state"] = tk.DISABLED
            return False

    def reset_query_button(self):
        """Restores the 'Submit Entry' button state from a previous disabling.
        In general this occurs while a query-request is being performed. This
        method is then called after the query has completed and results
        displayed.
        """
        self.entry_btn["state"] = tk.NORMAL
        self.entry_btn["command"] = self.search

    def modify_results_label(self, labeltxt, cnf={}):
        self.results_label["text"] = labeltxt
        for attr, valu in cnf.items():
            self.results_label[attr] = valu

    def resort_results(self, config_change=False):
        """This method is responsible for the ordering and display of queried
        results. It is called any time a query is submitted and when any
        sorting option is changed.
        """
        if config_change is True:
            self.save_defaults()

        self.results_label["foreground"] = "blue"
        self.results_label["text"] = "{} match{} {} found{}".format(
            len(self.results),
            "es" if len(self.results) != 1 else "",
            "were" if len(self.results) != 1 else "was",
            ", sorted by {}, ({})".format(
                self.sort_method.get(),
                "A to Z" if self.sort_direction.get() == 0 \
                    and self.sort_method.get() in ["id", "name", "state"] else \
                "Z to A" if self.sort_direction.get() == 1 \
                    and self.sort_method.get() in ["id", "name", "state"] else \
                "low-to-high" if self.sort_direction.get() == 0 else \
                "high-to-low"
            ) if len(self.results) > 1 else ""
        )

        # Clear results
        self.box_results.delete(0, tk.END)

        self.results.sort(
            key=lambda site: getattr(
                site,
                self.sort_method.get()
            ) if self.sort_method.get() != "state" \
            else str(getattr(
                site,
                self.sort_method.get()
            )),
            reverse = True if self.sort_direction.get() == 1 else False
        )

        # populate results
        for station in self.results:
            self.box_results.insert(
                tk.END,
                "{} - {}{} - {}".format(
                    station.id,
                    "{} - ".format(station.state) \
                        if station.state is not None else "",
                    station.name,
                    station.size
                )
            )
        self.verify_selection()

    def verify_selection(self, event=None):
        """This method is called, when needed, to manage the enabling and
        disabling of options to view station information or download.
        """
        if len(self.box_results.curselection()) == 1:
            self.station_info_btn["state"] = tk.NORMAL
            self.download_btn["state"] = tk.NORMAL
        else:
            self.station_info_btn["state"] = tk.DISABLED
            self.download_btn["state"] = tk.DISABLED

    def search_ready(self, event=None):
        """Runs a search if the search button is available to be pressed. This
        method is bound to the '<Return>' key.
        """
        if self.entry_btn["state"] != tk.DISABLED:
            self.search()

    def search(self):
        """Run a query on the database, based on data in the entry fields above
        the 'Submit Query' button.
        """

        # Disable submit query button temporarily to avoid flooding tk tasks
        self.entry_btn["state"] = tk.DISABLED
        self.entry_btn["command"] = None

        # clear results box
        self.box_results.delete(0, tk.END)
        self.results = []
        self.verify_selection()     # handles deactivating relevant buttons

        # for convenience; updates visuals for the buttons seemingly as query
        #   is being done.
        self.window.update_idletasks()

        # *************************************************************

        # Desciption entry contents
        desc = r'{}'.format(self.entry.get()) \
            if self.entry.get() != "" else None

        # Country/State entry contents
        if len(self.filter_state.get()) == 1:
            self.filter_state.delete(0, tk.END)
        country_abbr = self.filter_state.get().upper() \
            if len(self.filter_state.get()) > 0 else None

        # convenience bool to avoid the necessity of otherwise long attr
        bbox = True if self.coord_boundingbox_toggle.get() == 1 else False

        # Latitude 1 LOGIC - only appears if bbox is not toggled
        lat1_sign = self.lat_logic.get() if bbox is False else None

        # Latitude 1 Entry
        lat1 = int(self.lat_entry1.get()) \
            if self.lat_entry1.get() not in ["", "-"] else None

        # Longitude 1 LOGIC - only appears if bbox is not toggled
        lon1_sign = self.lon_logic.get() if bbox is False else None

        # Longitude 1
        lon1 = int(self.lon_entry1.get()) \
            if self.lon_entry1.get() not in ["", "-"] else None

        # Latitude 2
        lat2 = int(self.lat_entry2.get()) \
            if bbox is True and self.lat_entry2.get() not in ["", "-"] else None

        # Longitude 2
        lon2 = int(self.lon_entry2.get()) \
            if bbox is True and self.lon_entry2.get() not in ["", "-"] else None

        # Bool checking all coordinate entries for any content within
        anycoord = any(v is not None for v in [lat1, lat2, lon1, lon2])

        # Elevation entry
        elev = int(self.filter_elevation.get()) \
            if self.filter_elevation.get() != "" else None

        # *************************************************************

        def REGEXP(pattern, string):
            """SQLite3 Regular Expression function. Returns a bool indicating
            any matches for a Regular Expression.
            """
            return bool(
                re.search(
                    r'{}'.format(pattern),
                    r'{}'.format(string),
                    flags=re.I
                )
            )

        def IN_BBOX(test_lat, test_lon, _lat1, _lon1, _lat2, _lon2):
            """SQLite3 function that tests whether or not a given coordinate is
            contained within a bounding box formed by two other coordinates.
            Returns a bool reflecting the answer.
            """
            if min([_lat1, _lat2]) <= test_lat <= max([_lat1, _lat2]) \
            and min([_lon1, _lon2]) <= test_lon <= max([_lon1, _lon2]):
                return True
            else:
                return False

        # open the database
        db = sqlite3.connect(self.stations_db.name)

        # register custom functions
        db.create_function("REGEXP", 2, REGEXP)
        db.create_function("IN_BBOX", 6, IN_BBOX)

        # formulation of the exec_statement. This is done outside of the actual
        #   execute command to allow optional investigating of the command text
        exec_statement = "SELECT * FROM GHCNDaily WHERE " \
          + ("name REGEXP ? " if desc is not None else "") \
          + ("AND " \
                if desc is not None and country_abbr is not None \
                else "") \
          + ("(country = ? OR state = ?) " if country_abbr is not None else "") \
          + ("AND " \
                if (desc is not None or country_abbr is not None) \
                and (
                    (
                        bbox is False and \
                        (lat1 is not None or lon1 is not None)
                    ) or \
                    (
                        bbox is True and \
                        (lat1 is not None and lon1 is not None and \
                        lat2 is not None and lon2 is not None)
                    )
                ) else "") \
          + (
                "IN_BBOX(latitude, longitude, ?, ?, ?, ?) " if bbox is True \
                    and all([
                        lat1 is not None,
                        lat2 is not None,
                        lon1 is not None,
                        lon2 is not None
                    ]) else \
                "{}{}{}{}{}{}{}".format(
                    "latitude " if lat1 is not None and lat1_sign is not None else "",
                    "{} ".format(lat1_sign) \
                        if lat1_sign is not None and lat1 is not None else "",
                    "? " if lat1_sign is not None and lat1 is not None else "",
                    "AND " \
                        if lat1 is not None \
                        and lon1 is not None \
                        and lon1_sign is not None else "",
                    "longitude " if lon1 is not None and lon1_sign is not None else "",
                    "{} ".format(lon1_sign) \
                        if lon1_sign is not None and lon1 is not None else "",
                    "? " if lon1_sign is not None and lon1 is not None else "",
                )
            ) + ("AND " \
                if elev is not None and (
                    desc is not None or \
                    country_abbr is not None or \
                    anycoord is True
                ) else "") \
          + ("{}elevation {} {} {}{}".format(
                "(" if self.elev_logic.get() == "<=" else "",
                ">" if self.elev_logic.get() == "<=" else self.elev_logic.get(),
                -999 if self.elev_logic.get() == "<=" else "?",
                "AND elevation {} ?".format(self.elev_logic.get()) if self.elev_logic.get() == "<=" else "",
                ")" if self.elev_logic.get() == "<=" else ""
          ) if elev is not None else "")

        # *** DEBUG ***
        # print("---", exec_statement, "---", sep="\n")

        # Holds the arguments needed to pass to the execute function
        args = []
        coord_attrs = [lat1, lon1, lat2, lon2] if bbox is True and all([
                lat1 is not None,
                lat2 is not None,
                lon1 is not None,
                lon2 is not None
            ]) else []
        if bbox is False:
            if lat1 is not None: coord_attrs.append(lat1)
            if lon1 is not None: coord_attrs.append(lon1)
        for attr in [desc, country_abbr, country_abbr] + coord_attrs + [elev]:
            if attr is not None:
                args.append(attr)

        # *** DEBUG ***
        # print(args)

        # Record the results
        self.results = [
            self.stations[row[0]]
            for row in db.execute(exec_statement, args).fetchall()
        ]

        # close the database
        db.close()

        # Display the results
        if len(self.results) > 0:
            self.resort_results()
        else:
            self.modify_results_label(
                "* No Results Found! *",
                {"foreground": "red"}
            )

        # re-enable query search button
        self.entry_btn.after(100, self.reset_query_button)

    def download(self):
        """Download a GHCNDaily gzip file determined by selection in query-
        results list.
        """

        # Temporarily disable the download button to avoid flooding tk tasks
        self.download_btn["state"] = tk.DISABLED

        # The station of interest to download
        stn = self.results[self.box_results.curselection()[0]]

        # Formulate the download URL
        url = "".join([
            "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/by_station/",
            stn.id,
            ".csv.gz"
        ])

        # Formulate the name of the saved file; based on whether or not
        #   overwriting is requested
        if self.overwrite.get() is True:
            save_name = stn.id + ".csv.gz"
        else:
            save_name = "".join([
                stn.id,
                "_{:%Y%m%d-%H%M%S}".format(datetime.datetime.now()),
                ".csv.gz"
            ])

        # *** DEBUG ***
        # print(url)
        # print(save_name)

        # Initiate the download
        try:
            with urllib.request.urlopen(url, timeout=5) as u:
                with open(save_name, "wb") as w:
                    w.write(u.read())
            self.modify_results_label(
                "* Download of   '{}'   Successful! *".format(save_name),
                {"foreground": "green"}
            )
        except urllib.error.URLError:
            self.modify_results_label(
                "* Download of   '{}'   FAILED! *".format(save_name),
                {"foreground": "red"}
            )
            print("* Download of '{}' FAILED! ({})".format(
                save_name,
                url
            ))

        # re-enable download button
        self.download_btn.after(50, self.verify_selection)

ghcnd = GHCNDailyFinder()

















