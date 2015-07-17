#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  rest.py
#
#  Copyright 2014 Adam Fiebig <fiebig.adam@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

from compysition import Actor
from compysition.model.rest import RestEntityModel

class RestEntity(Actor):

    def __init__(self, name, model, *args, **kwargs):
        Actor.__init__(self, name, *args, **kwargs)
        self.model = model
        self.parents = None
        self.passthrough_methods = ["GET", "UPDATE", "PATCH"]

    def parse_url_at_current_step(self, url):
        parsed_url = {"next_entity": None,
                      "entity_key": None}

        url_steps = url.split("/")
        url_step_pos = url_steps.index(self.model.url_key)
        if url_step_pos < len(url_steps):
            if self.model.is_collection:
                url_step_pos += 1
                parsed_url["entity_key"] = url_steps[url_step_pos]

            if url_step_pos != len(url_steps):
                parsed_url["next_entity"] = url_steps[url_step_pos + 1]

        return parsed_url

    def consume(self, event, *args, **kwargs):
        current_step_properties = self.parse_url_at_current_step(event.http.url)

        self.validate_parents(event)
        # This isn't working, this is conceptual
        if event.get_the_current_rest_step == self.url_key:
            # Do work on this event
            pass
        if event.http.request_type in self.passthrough_methods:
            pass

    def validate_parents(self, event):
        """
        If all required parents have not been populated on l event
        no work may be done on this entity at this stage
        """
        for parent in self.model.parents:
            if isinstance(parent, RestEntityModel):
                if not getattr(event, str(parent.key), None):
                    return False

        return True

if __name__ == "__main__":
    model = RestEntityModel(url_key="applications", is_collection=True)
    entity = RestEntity("one", model)
    print entity.parse_url_at_current_step("/loans/applications/411231/decision")
