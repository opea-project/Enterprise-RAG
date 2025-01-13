// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      white: "#ffffff",
      black: "#000000",
      "classic-blue": {
        "-tint2": "#6cc4f5",
        "-tint1": "#0099ec",
        "-": "#0054ae",
        "-shade1": "#00377c",
        "-shade2": "#001e50",
      },
      "energy-blue": {
        "-tint2": "#a0ebff",
        "-tint1": "#6ddcff",
        "-": "#00c7fd",
        "-shade1": "#0095ca",
        "-shade2": "#005b85",
      },
      carbon: {
        "-tint2": "#e9e9e9",
        "-tint1": "#aeaeae",
        "-": "#808080",
        "-shade1": "#525252",
        "-shade2": "#262626",
      },
      "blue-steel": {
        "-tint2": "#b9d6e5",
        "-tint1": "#86b3ca",
        "-": "#548fad",
        "-shade1": "#41728a",
        "-shade2": "#183544",
      },
      geode: {
        "-tint2": "#eec3f7",
        "-tint1": "#cc94da",
        "-": "#8f5da2",
        "-shade1": "#653171",
      },
      moss: {
        "-tint2": "#d7f3a2",
        "-tint1": "#b1d272",
        "-": "#8bae46",
        "-shade1": "#708541",
        "-shade2": "#515a3d",
      },
      rust: {
        "-tint2": "#ffc599",
        "-tint1": "#ff8f51",
        "-": "#e96115",
        "-shade1": "#b24501",
      },
      cobalt: {
        "-tint2": "#98a1ff",
        "-tint1": "#5b69ff",
        "-": "#1e2eb8",
        "-shade1": "#000f8a",
        "-shade2": "#000864",
        "-shade3": "#040e35",
      },
      coral: {
        "-tint2": "#ffb6b9",
        "-tint1": "#ff848a",
        "-": "#ff5662",
        "-shade1": "#c81326",
      },
      daisy: {
        "-tint1": "#ffe17a",
        "-": "#fec91b",
        "-shade1": "#edb200",
        "-shade2": "#c98f00",
      },
      "light-gray": {
        50: "#ffffff",
        75: "#f9f9f9",
        100: "#f4f5f5",
        200: "#e9eaeb",
        300: "#e2e2e4",
        400: "#c9cace",
        500: "#b2b3b9",
        600: "#8b8e97",
        700: "#6a6d75",
        800: "#494b51",
        900: "#2b2c30",
      },
      "dark-gray": {
        50: "#242528",
        75: "#2e2f32",
        100: "#313236",
        200: "#3c3e42",
        300: "#484a50",
        400: "#585a62",
        500: "#6b6e76",
        600: "#8e9099",
        700: "#b7b9be",
        800: "#e3e3e5",
        900: "#ffffff",
      },
      status: {
        error: {
          primary: "#ce0000",
          natural: "#f5c7c7",
          soft: "#f88f8f",
          "natural-inverse": "#b13d4a",
          "soft-inverse": "#d55050",
        },
        success: {
          primary: "#008a00",
          natural: "#c2e5c2",
          soft: "#add2ad",
          "natural-inverse": "#006400",
          "soft-inverse": "#5ca05c",
        },
        warning: {
          primary: "#ffd100",
          natural: "#fff6cc",
          soft: "#ffeb92",
          "natural-inverse": "#ffeb92",
          "soft-inverse": "#ffe057",
        },
      },
    },
    extend: {
      colors: {
        // one tooltip style for both modes
        tooltip: {
          text: "#ffffff",
          background: "#242528",
        },
        light: {
          primary: "#0054AE",
          focus: "#0054AE",
          status: {
            success: {
              primary: "#008a00",
              soft: "#add2ad",
            },
            warning: {
              primary: "#ffd100",
              soft: "#ffeb92",
            },
            error: {
              primary: "#ce0000",
              soft: "#f88f8f",
            },
            unknown: {
              soft: "#b2b3b9",
              primary: "#6a6d75",
            },
          },
          background: {
            1: "#FFFFFF",
            2: "#F9F9F9",
            3: "#E9E9E9",
          },
          text: {
            primary: "#2b2c30",
            secondary: "#6a6d75",
            disabled: "#b2b3b9",
            placeholder: "#6a6d75",
            inverse: "#ffffff",
            error: "#da1e28",
          },
          link: {
            primary: "#0054ae",
            hover: "#00377c",
            visited: "#8f5da2",
          },
          button: {
            disabled: {
              text: "#B2B3B9",
              background: "#E9EAEB",
            },
            contained: {
              text: "#FFFFFF",
              primary: {
                background: "#0054AE",
                "background-hover": "#004A9D",
              },
              danger: {
                background: "#E43544",
                "background-hover": "#FF5662",
              },
            },
            outlined: {
              background: "#FFFFFF",
              "background-hover": "#E9EAEB",
              primary: {
                text: "#0054AE",
                border: "#0054AE",
                "border-hover": "#004A9D",
              },
              danger: {
                text: "#E43544",
                border: "#E43544",
                "border-hover": "#FF5662",
              },
            },
            icon: {
              ghost: {
                color: "#0054AE",
                hover: "#004A9D",
              },
              outlined: {
                background: "#FFFFFF",
                "color-hover": "#FFFFFF",
                "background-disabled": "#E9EAEB",
                "color-disabled": "#B2B3B9",
                primary: {
                  color: "#0054AE",
                  border: "#0054AE",
                  "background-hover": "#0054AE",
                  "border-hover": "#0054AE",
                },
                danger: {
                  color: "#E43544",
                  border: "#E43544",
                  "background-hover": "#E43544",
                  "border-hover": "#E43544",
                },
              },
            },
          },
          tabs: {
            "border-bottom": "#e2e2e4",
            button: {
              active: {
                "border-bottom": "#0054ae",
                text: "#2b2c30",
              },
              "not-active": {
                "border-bottom": "#8e9099",
                text: "#6a6d75",
              },
            },
          },
          input: {
            border: "#0054ae",
            text: "#2b2c30",
            background: "#ffffff",
            invalid: "#E43544",
            disabled: {
              background: "#E9EAEB",
              text: "#B2B3B9",
            },
          },
          notification: {
            text: "#ffffff",
            success: {
              background: "#006400",
            },
            error: {
              background: "#c81326",
            },
          },
          border: {
            subtle: "#e2e2e4",
            strong: "#8e9099",
            interactive: "#0054ae",
            inverse: "#161616",
            disabled: "#c6c6c6",
          },
        },
        dark: {
          primary: "#00c7fd",
          focus: "#00c7fd",
          status: {
            success: {
              primary: "#add2ad",
              soft: "#5ca05c",
            },
            warning: {
              primary: "#ffeb92",
              soft: "#ffe057",
            },
            error: {
              primary: "#f88f8f",
              soft: "#d55050",
            },
            unknown: {
              primary: "#6b6e76",
              soft: "#2b2c30",
            },
          },
          background: {
            1: "#242528",
            2: "#393939",
            3: "#525252",
          },
          text: {
            primary: "#ffffff",
            secondary: "#b7b9be",
            disabled: "#6b6e76",
            inverse: "#2b2c30",
            placeholder: "#b7b9be",
            error: "#ff5662",
          },
          link: {
            primary: "#00c7fd",
            hover: "#87E4FF",
            visited: "#eec3f7",
          },
          button: {
            disabled: {
              text: "#6B6E76",
              background: "#3C3E42",
            },
            contained: {
              text: "#2B2C30",
              primary: {
                background: "#00C7FD",
                "background-hover": "#87E4FF",
              },
              danger: {
                background: "#FF5662",
                "background-hover": "#FF5662",
              },
            },
            outlined: {
              background: "transparent",
              "background-hover": "#3C3E42",
              primary: {
                text: "#00C7FD",
                border: "#00C7FD",
                "border-hover": "#87E4FF",
              },
              danger: {
                text: "#FF5662",
                border: "#FF5662",
                "border-hover": "#FF5662",
              },
            },
            icon: {
              ghost: {
                color: "#00c7fd",
                hover: "#87E4FF",
              },
              outlined: {
                background: "#242528",
                "background-disabled": "#3C3E42",
                "color-disabled": "#6B6E76",
                "color-hover": "#242528",
                primary: {
                  color: "#00c7fd",
                  border: "#00c7fd",
                  "background-hover": "#00c7fd",
                  "border-hover": "#00c7fd",
                },
                danger: {
                  color: "#ff5662",
                  border: "#ff5662",
                  "background-hover": "#ff5662",
                  "border-hover": "#ff5662",
                },
              },
            },
          },
          tabs: {
            "border-bottom": "#484a50",
            button: {
              active: {
                "border-bottom": "#00c7fd",
                text: "#ffffff",
              },
              "not-active": {
                "border-bottom": "#8e9099",
                text: "#b7b9be",
              },
            },
          },
          input: {
            border: "#00c7fd",
            text: "#FFFFFF",
            background: "#242528",
            invalid: "#ff5662",
            disabled: {
              background: "#525252",
              text: "#6b6e76",
            },
          },
          notification: {
            text: "#2b2c30",
            success: {
              background: "#5ca05c",
            },
            error: {
              background: "#ff5662",
            },
          },
          border: {
            subtle: "#484a50",
            strong: "#8e9099",
            interactive: "#00c7fd",
            inverse: "#8e9099",
            disabled: "#8d8d8d",
          },
        },
        break: {},
      },
    },
  },
  plugins: [],
};
