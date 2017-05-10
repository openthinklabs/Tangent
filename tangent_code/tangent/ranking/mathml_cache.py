"""
    Tangent
   Copyright (c) 2013, 2015 David Stalnaker, Richard Zanibbi, Nidhin Pattaniyil, 
                  Andrew Kane, Frank Tompa, Kenny Davila Castellanos

    This file is part of Tangent.

    Tanget is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tangent is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tangent.  If not, see <http://www.gnu.org/licenses/>.

    Contact:
        - Richard Zanibbi: rlaz@cs.rit.edu
"""

__author__ = 'KDavila'

from tangent.utility.control import Control
from tangent.math.mathdocument import MathDocument
from tangent.math.math_extractor import MathExtractor


class MathMLCache:
    def __init__(self, control_filename):
        self.control_filename = control_filename
        self.cached_locations = {}
        self.cached_expressions = {}

    def get(self, doc_id, location, expression, force_update=False):
        if not doc_id in self.cached_locations:
            self.cached_locations[doc_id] = {}

        if location in self.cached_locations[doc_id] and not force_update:
            return self.cached_locations[doc_id][location]
        else:
            #first time the expression is seen, check....

            if expression in self.cached_expressions and not force_update:
                #expression has been retrieved before but at different location...
                prev_doc_id, prev_location = self.cached_expressions[expression]

                return self.cached_locations[prev_doc_id][prev_location]
            else:

                control = Control(self.control_filename) # control file name (after indexing)
                document_finder = MathDocument(control)

                mathml = document_finder.find_mathml(doc_id, location)
                mathml = MathExtractor.isolate_pmml(mathml)
                if isinstance(mathml, bytes):
                    mathml = mathml.decode('UTF-8')

                # save on cache...
                self.cached_locations[doc_id][location] = mathml
                self.cached_expressions[expression] = (doc_id, location)

                return mathml
