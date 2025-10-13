import "./SearchBar.scss";

import { ClearIcon, SearchIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import debounce from "lodash.debounce";
import {
  ChangeEvent,
  HTMLAttributes,
  useCallback,
  useEffect,
  useState,
} from "react";

const DEBOUNCE_MS = 100;

interface SearchBarProps
  extends Omit<HTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}

export const SearchBar = ({
  value,
  className,
  placeholder,
  onChange,
}: SearchBarProps) => {
  const [inner, setInner] = useState(value);

  useEffect(() => setInner(value), [value]);

  const debouncedOnChange = useCallback(
    debounce((newValue: string) => onChange(newValue), DEBOUNCE_MS),
    [onChange],
  );

  useEffect(() => {
    debouncedOnChange(inner);
  }, [inner, debouncedOnChange]);

  const onInput = (e: ChangeEvent<HTMLInputElement>) => {
    setInner(e.target.value);
  };

  const handleClear = () => {
    setInner("");
    debouncedOnChange("");
  };

  return (
    <div className={classNames("search-bar", className)}>
      <SearchIcon size={9} className="search-bar__icon" />
      <input
        type="text"
        className="search-bar__input"
        placeholder={placeholder}
        value={inner}
        aria-label="Global table search"
        onChange={onInput}
      />
      {inner && (
        <ClearIcon
          size={9}
          className="search-bar__clear-icon"
          onClick={handleClear}
        />
      )}
    </div>
  );
};
