// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./HomoglyphTextMarker.scss";

interface HomoglyphTextMarkerProps {
  text: string;
}

const HomoglyphTextMarker = ({ text }: HomoglyphTextMarkerProps) => (
  <mark className="homoglyph-text" title="Potential homoglyphs. Be cautious.">
    {text}
  </mark>
);

export default HomoglyphTextMarker;
