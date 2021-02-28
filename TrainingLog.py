import pandas as pd
import csv
from content.presets import *
from collections import namedtuple
import json
from pathlib import Path

Workout_tuple = namedtuple("Workout_tuple", "tag, exercises")


class TrainingPlan():
    """
    Reads in a sequence of workouts and fits them to training days.
    Automates progression in terms of overload or rpe. SUbclasses for specific paradigms.
    """

    def __init__(self):
        self.workouts = {}
        self.times = t_times

    def add_workout(workout):
        self.workouts[workout.id] = workout.exercises


class StartingStrengh(TrainingPlan):
    plan = pd.DataFrame(columns=["DateTime", "Workout", "Excercises"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shoulderpess = cur_shoulderpress
        self.row = cur_row
        self.benchpress = cur_benchpress
        self.squat = cur_squat
        self.deadlift = cur_deadlift
        # Placeholder for testing
        self.workouts = [WorkOut(tag="Leg", exercises=[Squat(overload=5), DeadLift(overload=5)]),
                         WorkOut(tag="Overhead", exercises=[ShoulderPress()]),
                         WorkOut(tag="Bench", exercises=[Squat(), BenchPress(), Row()])]
        self.training = None

    def _create_blank_plan(self, start, cycles):
        """
        Use preset trainingdays as businessdays.
        Return timeseries of appropriate length.
        """
        start = pd.to_datetime(start)
        trainingdays = " ".join(list(t_times.keys()))
        tdays = pd.offsets.CustomBusinessDay(weekmask=trainingdays)
        series = pd.Series(pd.date_range(start, periods=cycles * len(self.workouts),
                                         freq=tdays))
        return series

    def _apply_overload(self, df, index):
        df.loc[index, "weight"] += df.loc[index,
                                          "cycle"] * df.loc[index, "overload"]

    def create_workout_frame(self, start, cycles):
        """
        Create Dataframe and loop over workouts for however many cycles are spedcified. Update Dataframe with new row for each exercise. Go through the full plan and apply overload dependend on current cycle.
        """

        header = ["date", "id", "name", "tag", "cycle", "weight",
                  "reps", "sets", "rest", "superset", "overload", "Note"]
        temp_plan = pd.DataFrame(columns=header)
        t_series = self._create_blank_plan(start, cycles)
        t_position = 0
        for cycle in range(cycles):
            for workout in self.workouts:
                frame_dict = {
                    "date": t_series[t_position], "id": workout.data.tag, "cycle": cycle}
                t_position += 1
                for exercise in workout.data.exercises:
                    frame_dict.update(vars(exercise))
                    temp_plan = temp_plan.append(frame_dict, ignore_index=True)
        result = [self._apply_overload(temp_plan, i) for i in temp_plan.index]
        self.training = temp_plan

    def object_from_df(self):
        # take specified row, recreate object
        pass

    def frame_to_json(self):
        json_plan = self.training.to_json(orient="records")
        parsed = json.loads(json_plan)
        with open(Path.cwd() / "content" / "plans" / "starting_strengh.json", "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=4)

    def frame_from_json(self):
        self.training = pd.read_json(
            Path.cwd() / "content" / "plans" / "starting_strengh.json")

    def adjust_weight(self, date, lift, new_weight, cascade=True):
        """
        In case of a missed lift, correct the number on the the day and cascade the change in expectation down through the plan.
        """
        if cascade:
            filt = self.training.loc[(self.training.name == lift) & (
                self.training.date >= date)]
            for e, i in enumerate(filt.index):
                self.training.loc[i, "weight"] = new_weight + \
                    e * self.training.loc[i, "overload"]
        else:
            self.training.loc[(self.training.name == lift) & (
                self.training.date == date), "weight"] = new_weight


class WorkOut():
    """
    Colletion of exercises with specific values. Created manually and saved
    to presets or read in from presets.
    """

    def __init__(self, tag=None, exercises=[]):
        self.id = tag
        self.exercises = exercises
        self.data = Workout_tuple(tag=self.id, exercises=self.exercises)

    def __str__(self):
        printout = ""
        for exercise in self.exercises:
            printout += f"{exercise}\n"
        return printout

    def add_exercise(self, choice):
        self.exercises.append(choice)
        self.data = Workout_tuple(self.id, self.exercises)

    def remove_excercice(self, choice):
        self.exercises.remove(choice)
        self.data = Workout_tuple(self.id, self.exercises)


class Excercise():
    """
    Initialized with standart values from content.presets if not otherwise specified. Intended for subclassing and not used directly.
    """

    def __init__(self, reps=def_reps, sets=def_sets, rest=def_rest, superset=False, overload=2.5):
        self.reps = reps
        self.sets = sets
        self.rest = rest
        self.superset = superset
        self.overload = overload

    def __repr__(self):
        return f"{self.name} at {self.weight} kg for {self.reps} reps. {self.sets} sets."

    def __str__(self):
        return f"{self.name} at {self.weight} kg for {self.reps} reps. {self.sets} sets."


class ShoulderPress(Excercise):

    def __init__(self, weight=max_shoulderpress, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag = "main_lift"
        self.name = "ShoulderPress"
        self.weight = weight


class Row(Excercise):

    def __init__(self, weight=max_row, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag = "main_lift"
        self.name = "Row"
        self.weight = weight


class BenchPress(Excercise):

    def __init__(self, weight=max_benchpress, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag = "main_lift"
        self.name = "BenchPress"
        self.weight = weight


class Squat(Excercise):

    def __init__(self, weight=max_squat, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag = "main_lift"
        self.name = "Squat"
        self.weight = weight


class DeadLift(Excercise):

    def __init__(self, weight=max_deadlift, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag = "main_lift"
        self.name = "DeadLift"
        self.weight = weight


if __name__ == "__main__":
    plan = StartingStrengh()
    plan.create_workout_frame("2021-01-22", 4)
    print(plan.training)
    plan.frame_to_json()
