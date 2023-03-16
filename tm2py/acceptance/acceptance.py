"""Methods to create Acceptance Criteria summaries from a tm2py model run."""

from tm2py.acceptance.simulated import Simulated
from tm2py.acceptance.observed import Observed
from tm2py.acceptance.canonical import Canonical

import numpy as np
import os
import geopandas as gpd
import itertools
import pandas as pd

class Acceptance:

    s: Simulated
    o: Observed
    c: Canonical

    acceptance_output_folder_root: str

    output_transit_filename = "acceptance-transit-network.geojson"
    output_other_filename = "acceptance-other.geojson"

    tableau_projection = "4326"

    # Output data specs
    road_network_gdf = gpd.GeoDataFrame(
        {
            "model_link_id": pd.Series(dtype="int"),
            "pems_station_id": pd.Series(dtype="int"),
            "time_period": pd.Series(dtype="str"),
            "observed_flow": pd.Series(dtype="float"),
            "simulated_flow": pd.Series(dtype="float"),
            "odot_flow_category": pd.Series(dtype="int"),
            "odot_maximum_error": pd.Series(dtype="float"),
            "geometry": pd.Series(dtype="str"),  # line
        }
    )

    transit_network_gdf = gpd.GeoDataFrame(
        {
            "model_link_id": pd.Series(dtype="int"),
            "model_line_id": pd.Series(dtype="str"),
            "operator": pd.Series(dtype="str"),
            "technology": pd.Series(dtype="str"),
            "route_short_name": pd.Series(dtype="str"),
            "route_long_name": pd.Series(dtype="str"),
            "trip_headsign": pd.Series(dtype="str"),
            "time_period": pd.Series(dtype="str"),
            "route_observed_boardings": pd.Series(dtype="float"),
            "route_simulated_boardings": pd.Series(dtype="float"),
            "florida_threshold": pd.Series(dtype="float"),
            "am_segment_simulated_boardings": pd.Series(dtype="float"),
            "am_segment_volume": pd.Series(dtype="float"),
            "am_segment_capacity_total": pd.Series(dtype="float"),
            "am_segment_vc_ratio_total": pd.Series(dtype="float"),
            "am_segment_capacity_seated": pd.Series(dtype="float"),
            "am_segment_vc_ratio_seated": pd.Series(dtype="float"),
            "mean_am_segment_vc_ratio_total": pd.Series(dtype="float"),
            "geometry": pd.Series(dtype="str"),  # lines
        }
    )

    compare_gdf = gpd.GeoDataFrame(
        {
            "criteria_number": pd.Series(dtype="int"),
            "criteria_name": pd.Series(dtype="str"),
            "dimension_01_name": pd.Series(dtype="str"),
            "dimension_01_value": pd.Series(dtype="float"),
            "dimension_02_name": pd.Series(dtype="str"),
            "dimension_02_value": pd.Series(dtype="float"),
            "dimension_03_name": pd.Series(dtype="str"),
            "dimension_03_value": pd.Series(dtype="float"),
            "observed_outcome": pd.Series(dtype="float"),
            "simulated_outcome": pd.Series(dtype="float"),
            "acceptance_threshold": pd.Series(dtype="float"),
            "geometry": pd.Series(dtype="str"),  # point
        }
    )

    def __init__(self, canonical: Canonical, simulated: Simulated, observed: Observed, output_file_root: str) -> None:
        self.c = canonical
        self.s = simulated
        self.o = observed
        self.acceptance_output_folder_root = output_file_root

    def make_acceptance(
        self, make_transit=True, make_roadway=True, make_other=False
    ):
        if make_roadway:
            # self._make_roadway_acceptance()
            pass
        if make_transit:
            self._make_transit_network_comparisons()
        if make_other:
            self._make_other_comparisons()

        return


    def _write_roadway_network():
        """_summary_
        Method to set the geometry of the geopandas object and write the file to disk.
        """

        # set the geometry
        # make sure it is in the right projection
        # get the file location from the dictionary
        # write to disk

        return

    def _write_transit_network(self):

        file_root = self.acceptance_output_folder_root
        # TODO: figure out how to get remote write, use . for now
        file_root = "."
        out_file = os.path.join(file_root, self.output_transit_filename)
        self.transit_network_gdf.to_file(out_file, driver="GeoJSON")

        return

    def _write_other_comparisons(self):

        file_root = self.acceptance_output_folder_root
        # TODO: figure out how to get remote write, use . for now
        file_root = "."
        out_file = os.path.join(file_root, self.output_other_filename)
        self.compare_gdf.to_file(out_file, driver="GeoJSON")

        return

    def _make_roadway_network_comparisons():

        # placeholder
        # _write_roadway_network()

        return

    def _make_transit_network_comparisons(self):

        # step 1: outer merge for rail operators (ignore route)
        obs_df = self.o.reduced_transit_on_board_df[
            self.o.reduced_transit_on_board_df["survey_operator"].isin(
                self.c.rail_operators_vector
            )
        ].copy()

        obs_df = obs_df[
            [
                "survey_tech",
                "survey_operator",
                "survey_route",
                "survey_boardings",
                "time_period",
                "florida_threshold",
            ]
        ].rename(columns={"survey_operator": "operator", "survey_tech": "technology"})
        obs_df = self._fix_technology_labels(obs_df, "technology")

        sim_df = (
            self.s.simulated_boardings_df[
                self.s.simulated_boardings_df["operator"].isin(self.c.rail_operators_vector)
            ]
            .groupby(["tm2_mode", "line_mode", "operator", "technology", "time_period"])
            .agg({"total_boarding": "sum"})
            .reset_index()
        )

        rail_df = pd.merge(
            sim_df,
            obs_df,
            how="outer",
            on=["operator", "technology", "time_period"],
        )

        # step 2: left merge for non-rail operators
        obs_df = self.o.reduced_transit_on_board_df[
            ~self.o.reduced_transit_on_board_df["survey_operator"].isin(
                self.c.rail_operators_vector
            )
        ].copy()
        sim_df = self.s.simulated_boardings_df[
            ~self.s.simulated_boardings_df["operator"].isin(self.c.rail_operators_vector)
        ].copy()

        non_df = pd.merge(
            sim_df,
            obs_df,
            how="left",
            left_on=["line_name", "daily_line_name", "time_period"],
            right_on=["standard_line_name", "daily_line_name", "time_period"],
        )

        boards_df = pd.concat([rail_df, non_df])

        boards_df["operator"] = np.where(
            boards_df["operator"].isnull(),
            boards_df["survey_operator"],
            boards_df["operator"],
        )
        boards_df["technology"] = np.where(
            boards_df["technology"].isnull(),
            boards_df["survey_tech"],
            boards_df["technology"],
        )

        # step 3 -- create a daily shape
        df = pd.DataFrame(self.s.simulated_transit_segments_gdf).copy()
        am_shape_df = df[~(df["line"].str.contains("pnr_"))].reset_index().copy()
        am_shape_df = self.c.aggregate_line_names_across_time_of_day(am_shape_df, "line")
        b_df = (
            am_shape_df.groupby("daily_line_name")
            .agg({"line": "first"})
            .reset_index()
            .copy()
        )
        c_df = pd.DataFrame(
            self.s.simulated_transit_segments_gdf[
                self.s.simulated_transit_segments_gdf["line"].isin(b_df["line"])
            ].copy()
        )
        daily_shape_df = pd.merge(c_df, b_df, how="left", on="line")

        # step 4 -- join the shapes to the boardings
        # for daily, join boardings to shape, as I care about the boardings more than the daily shapes
        daily_join_df = pd.merge(
            boards_df[boards_df["time_period"] == self.c.ALL_DAY_WORD],
            daily_shape_df,
            how="left",
            on="daily_line_name",
        )
        daily_join_df["model_line_id"] = daily_join_df["daily_line_name"]
        daily_join_df["time_period"] = np.where(
            daily_join_df["time_period"].isnull(),
            self.c.ALL_DAY_WORD,
            daily_join_df["time_period"],
        )

        # for am, join shapes to boardings, as I care more about the shapes volumes than the am boardings
        am_join_df = pd.merge(
            am_shape_df,
            boards_df[boards_df["time_period"] == "am"],
            how="left",
            right_on=["line_name", "daily_line_name"],
            left_on=["line", "daily_line_name"],
        )
        am_join_df["model_line_id"] = am_join_df["line_name"]
        am_join_df["time_period"] = np.where(
            am_join_df["time_period"].isnull(), "am", am_join_df["time_period"]
        )
        am_join_df = self.s._get_operator_name_from_line_name(
            am_join_df, "line", "temp_operator"
        )
        am_join_df["operator"] = np.where(
            am_join_df["operator"].isnull()
            & am_join_df["temp_operator"].isin(self.c.rail_operators_vector),
            am_join_df["temp_operator"],
            am_join_df["operator"],
        )

        return_df = pd.concat(
            [daily_join_df, am_join_df], axis="rows", ignore_index=True
        )

        return_df = return_df.rename(
            columns={
                "#link_id": "model_link_id",
                "standard_route_short_name": "route_short_name",
                "standard_route_long_name": "route_long_name",
                "standard_headsign": "trip_headsign",
                "description": "line_description",
                "survey_boardings": "route_observed_boardings",
                "total_boarding": "route_simulated_boardings",
                "board": "am_segment_simulated_boardings",
            }
        )

        # only attach route-level boardings to first link
        return_df["route_simulated_boardings"] = np.where(
            return_df["first_row_in_line"], return_df["route_simulated_boardings"], 0
        )
        return_df["route_observed_boardings"] = np.where(
            return_df["first_row_in_line"], return_df["route_observed_boardings"], 0
        )

        # TODO: remove this once the crosswalk with direction is made
        return_df["route_observed_boardings"] = np.where(
            return_df["time_period"] == "am", 0, return_df["route_observed_boardings"]
        )

        return_df = self._fix_technology_labels(return_df, "technology")

        return_df = return_df[self.transit_network_gdf.columns]

        self.transit_network_gdf = gpd.GeoDataFrame(
            return_df, crs="EPSG:" + self.tableau_projection, geometry="geometry"
        )

        self._write_transit_network()

        return

    def _make_other_comparisons(self):

        a_df = self._make_home_work_flow_comparisons()
        b_gdf = self._make_zero_vehicle_household_comparisons()
        c_gdf = self._make_bart_station_to_station_comparisons()
        d_gdf = self._make_rail_access_comparisons()

        self.compare_gdf = gpd.GeoDataFrame(
            pd.concat([a_df, b_gdf, c_gdf, d_gdf]), geometry="geometry"
        )

        self._write_other_comparisons()

        return

    def _fix_technology_labels(
        self, input_df: pd.DataFrame, column_name: str
    ) -> pd.DataFrame:

        assert column_name in input_df.columns

        r_df = input_df.copy()

        fix_dict = {
            "local": "Local Bus",
            "express": "Express Bus",
            "light": "Light Rail",
            "ferry": "Ferry",
            "heavy": "Heavy Rail",
            "commuter": "Commuter Rail",
        }

        for key, value in fix_dict.items():
            r_df[column_name] = np.where(
                r_df[column_name].str.lower().str.contains(key),
                value,
                r_df[column_name],
            )

        return r_df

    def _make_home_work_flow_comparisons(self):

        adjust_observed = (
            self.s.simulated_home_work_flows_df.simulated_flow.sum()
            / self.o.ctpp_2012_2016_df.observed_flow.sum()
        )
        j_df = self.o.ctpp_2012_2016_df.copy()
        j_df["observed_flow"] = j_df["observed_flow"] * adjust_observed

        df = pd.merge(
            self.s.simulated_home_work_flows_df,
            j_df,
            how="left",
            on=["residence_county", "work_county"],
        )

        df["criteria_number"] = 23
        df["acceptance_threshold"] = "Less than 15 percent RMSE"
        df[
            "criteria_name"
        ] = "Percent root mean square error in CTPP county-to-county worker flows"
        df["dimension_01_name"] = "residence_county"
        df["dimension_02_name"] = "work_county"
        df = df.rename(
            columns={
                "residence_county": "dimension_01_value",
                "work_county": "dimension_02_value",
                "observed_flow": "observed_outcome",
                "simulated_flow": "simulated_outcome",
            }
        )

        return df

    def _make_zero_vehicle_household_comparisons(self):

        # prepare simulated data
        a_df = (
            pd.merge(
                self.s.simulated_zero_vehicle_hhs_df,
                self.s.simulated_maz_data_df[["MAZ_ORIGINAL", "MAZSEQ"]],
                left_on="maz",
                right_on="MAZSEQ",
                how="left",
            )
            .drop(columns=["maz", "MAZSEQ"])
            .rename(columns={"MAZ_ORIGINAL": "maz"})
        )

        # TODO: probably better if this is done in Simulated, to avoid using Canonical in this class
        a_df = pd.merge(
            a_df,
            self.c.census_2010_to_maz_crosswalk_df,
            how="left",
            on="maz",
        )

        a_df["product"] = a_df["simulated_zero_vehicle_share"] * a_df["maz_share"]

        b_df = (
            a_df.groupby("blockgroup")
            .agg({"product": "sum", "simulated_households": "sum"})
            .reset_index()
            .rename(columns={"product": "simulated_zero_vehicle_share"})
        )
        b_df["tract"] = b_df["blockgroup"].astype("str").str.slice(stop=-1)
        b_df["product"] = (
            b_df["simulated_zero_vehicle_share"] * b_df["simulated_households"]
        )

        c_df = (
            b_df.groupby("tract")
            .agg({"product": "sum", "simulated_households": "sum"})
            .reset_index()
        )
        c_df["simulated_zero_vehicle_share"] = (
            c_df["product"] / c_df["simulated_households"]
        )

        # prepare the observed data
        join_df = self.o.census_2017_zero_vehicle_hhs_df.copy()
        join_df["tract"] = join_df["geoid"].str.replace("1400000US0", "")
        join_df = join_df[
            ["tract", "total_households", "observed_zero_vehicle_household_share"]
        ].drop_duplicates()

        df = pd.merge(
            c_df[["tract", "simulated_zero_vehicle_share"]],
            join_df,
            how="left",
            on="tract",
        )

        df = pd.merge(df, self.o.census_tract_centroids_gdf, how="left", on="tract")

        df["criteria_number"] = 24
        df["acceptance_threshold"] = "MTC's Assessment of Reasonableness"
        df[
            "criteria_name"
        ] = "Spatial patters of observed and estimated zero vehicle households"
        df["dimension_01_name"] = "residence_tract"
        df["dimension_02_name"] = "observed_total_households"
        df = df.rename(
            columns={
                "tract": "dimension_01_value",
                "total_households": "dimension_02_value",
                "observed_zero_vehicle_household_share": "observed_outcome",
                "simulated_zero_vehicle_share": "simulated_outcome",
            }
        )

        gdf = gpd.GeoDataFrame(df, geometry="geometry")

        return gdf

    def _make_bart_station_to_station_comparisons(self):

        s_df = self.s.simulated_station_to_station_df.copy()

        df = pd.merge(
            self.o.observed_bart_boardings_df,
            s_df[s_df["operator"] == "BART"].drop(columns=["operator"]),
            left_on=["boarding", "alighting"],
            right_on=["boarding_name", "alighting_name"],
        ).drop(columns=["boarding_name", "alighting_name"])

        df["criteria_number"] = 16
        df[
            "criteria_name"
        ] = "Percent root mean square error across boarding-alighting BART flows"
        df["acceptance_threshold"] = "Less than 40 percent"
        df["dimension_01_name"] = "Boarding Station"
        df["dimension_02_name"] = "Alighting Station"

        df = df.rename(
            columns={
                "boarding": "dimension_01_value",
                "alighting": "dimension_02_value",
                "observed": "observed_outcome",
                "simulated": "simulated_outcome",
            }
        )

        r_gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df["boarding_lon"], df["boarding_lat"])
        ).drop(columns=["boarding_lon", "boarding_lat"])

        return r_gdf

    def _make_rail_access_comparisons(self):

        PARK_AND_RIDE_OBSERVED_THRESHOLD = 500

        s_df = self.s.simulated_transit_access_df.copy()
        o_df = self.o.reduced_transit_on_board_access_df.copy()

        s_df["access_mode"] = s_df["access_mode"].map(self.s.transit_access_mode_dict)
        o_df["access_mode"] = o_df["access_mode"].map(self.s.transit_access_mode_dict)

        # am for now
        join_df = pd.merge(
            o_df[o_df["time_period"] == "am"],
            s_df[s_df["time_period"] == "am"],
            how="left",
            left_on=["operator", "boarding_station", "time_period", "access_mode"],
            right_on=["operator", "boarding_name", "time_period", "access_mode"],
        )

        join_df["simulated_boardings"] = join_df["simulated_boardings"].fillna(0)

        a_df = join_df[join_df["access_mode"] == "Park and Ride"].copy()
        b_df = a_df[a_df["survey_trips"] > PARK_AND_RIDE_OBSERVED_THRESHOLD].copy()
        relevant_station_df = b_df[["operator", "boarding_station"]].reset_index(
            drop=True
        )

        df = (
            join_df[
                join_df["operator"].isin(relevant_station_df["operator"])
                & join_df["boarding_station"].isin(
                    relevant_station_df["boarding_station"]
                )
            ]
            .copy()
            .reset_index(drop=True)
        )

        # TODO: do this on the simulation side rather than here
        df = self.s._join_coordinates_to_stations(df, "boarding")

        df["criteria_number"] = 19
        df[
            "criteria_name"
        ] = "Percent error in share of transit boardings that access via walk, bus, park and ride, and kiss and ride at rail stations"
        df["acceptance_threshold"] = "MTC's assessment of reasonableness"
        df["dimension_01_name"] = "Boarding Station"
        df["dimension_02_name"] = "Access Mode"

        df["dimension_01_value"] = df["operator"] + " " + df["boarding_station"]

        df = df.rename(
            columns={
                "access_mode": "dimension_02_value",
                "survey_trips": "observed_outcome",
                "simulated_boardings": "simulated_outcome",
            }
        )

        # add criteria 17, which will use the same data
        pnr_df = df[df["operator"] == "BART"].copy()
        pnr_df = pnr_df[pnr_df["dimension_02_value"] == "Park and Ride"].copy()
        pnr_df["criteria_number"] = 17
        pnr_df[
            "criteria_name"
        ] = "Percent root mean square error in park and ride lot demand at each BART station with parking access."
        pnr_df[
            "acceptance_threshold"
        ] = "Less than 20 percent for lots with more than 500 daily vehicles"
        pnr_df["dimension_01_name"] = "Boarding Station"
        pnr_df["dimension_01_value"] = pnr_df["boarding_station"]

        # for criteria 19
        df = df.drop(
            columns=[
                "operator",
                "boarding_station",
                "time_period",
            ]
        )

        # for criteria 17
        pnr_df = pnr_df.drop(
            columns=[
                "operator",
                "boarding_station",
                "time_period",
                "dimension_02_value",
                "dimension_02_name",
            ]
        )

        both_df = pd.concat([df, pnr_df], ignore_index=True)

        r_gdf = gpd.GeoDataFrame(
            both_df,
            geometry=gpd.points_from_xy(
                both_df["boarding_lon"], both_df["boarding_lat"]
            ),
        ).drop(columns=["boarding_lon", "boarding_lat"])

        return r_gdf
