
class PeopleCounter:
    def __init__(
        self,
        line_position=0.5,
        margin=20,
        confirmation_frames=3
    ):
        self.people_inside = 0
        self.total_entered = 0
        self.total_exited = 0

        self.line_position = line_position
        self.margin = margin
        self.confirmation_frames = confirmation_frames

        self.tracked_people = {}
        self.frame_number = 0

    def update(self, people, frame_width):
        self.frame_number += 1

        line_x = int(frame_width * self.line_position)

        for person in people:
            track_id = person["id"]
            x1, y1, x2, y2 = person["box"]

            center_x = (x1 + x2) // 2

            # Determine which side of the line
            if center_x < line_x - self.margin:
                current_side = -1
            elif center_x > line_x + self.margin:
                current_side = 1
            else:
                current_side = 0

            if track_id not in self.tracked_people:
                self.tracked_people[track_id] = {
                    "confirmed_side": current_side,
                    "candidate_side": 0,
                    "candidate_frames": 0,
                    "last_seen": self.frame_number
                }
                continue

            data = self.tracked_people[track_id]
            data["last_seen"] = self.frame_number

            if current_side == 0:
                continue

            # No previous confirmed side?
            if data["confirmed_side"] == 0:
                data["confirmed_side"] = current_side
                continue

            # Person remains on their current side
            if current_side == data["confirmed_side"]:
                data["candidate_side"] = 0
                data["candidate_frames"] = 0
                continue

            # Person is moving towards the opposite side
            if current_side != data["candidate_side"]:
                data["candidate_side"] = current_side
                data["candidate_frames"] = 1
            else:
                data["candidate_frames"] += 1

            # Confirm crossing only after several frames
            if data["candidate_frames"] >= self.confirmation_frames:

                previous_side = data["confirmed_side"]
                new_side = data["candidate_side"]

                if previous_side == -1 and new_side == 1:
                    self.people_inside += 1
                    self.total_entered += 1
                    print(f"Person {track_id} entered!")

                elif previous_side == 1 and new_side == -1:
                    self.people_inside = max(
                        0, self.people_inside - 1
                    )
                    self.total_exited += 1
                    print(f"Person {track_id} exited!")

                data["confirmed_side"] = new_side
                data["candidate_side"] = 0
                data["candidate_frames"] = 0

        # Remove expired tracks
        expired_ids = [
            track_id
            for track_id, data in self.tracked_people.items()
            if self.frame_number - data["last_seen"] > 180
        ]

        for track_id in expired_ids:
            del self.tracked_people[track_id]

        return {
            "inside": self.people_inside,
            "entered": self.total_entered,
            "exited": self.total_exited,
            "line_x": line_x
        }
