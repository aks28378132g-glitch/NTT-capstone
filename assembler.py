
import sys
from pathlib import Path

# Hack Assembly predefined symbols
symbols = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "SCREEN": 16384, "KBD": 24576
}

for i in range(16):
    symbols[f"R{i}"] = i

# Hack C-instruction tables
comp = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "M": "1110000",
    "!D": "0001101", "!A": "0110001", "!M": "1110001",
    "-D": "0001111", "-A": "0110011", "-M": "1110011",
    "D+1": "0011111", "A+1": "0110111", "M+1": "1110111",
    "D-1": "0001110", "A-1": "0110010", "M-1": "1110010",
    "D+A": "0000010", "D+M": "1000010",
    "D-A": "0010011", "D-M": "1010011",
    "A-D": "0000111", "M-D": "1000111",
    "D&A": "0000000", "D&M": "1000000",
    "D|A": "0010101", "D|M": "1010101"
}

dest = {
    "": "000", "M": "001", "D": "010", "MD": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111"
}

jump = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"
}


def clean_lines(source):
    result = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        line = line.split("//")[0].strip()
        if line:
            result.append((line_no, line))
    return result


def assemble(filename):
    path = Path(filename)
    source = path.read_text(encoding="utf-8")
    lines = clean_lines(source)

    # Pass 1: find labels
    rom_address = 0
    for line_no, line in lines:
        if line.startswith("(") and line.endswith(")"):
            label = line[1:-1].strip()
            if label in symbols:
                print(f"Warning: duplicate label '{label}' at line {line_no}")
            else:
                symbols[label] = rom_address
        else:
            rom_address += 1

    # Pass 2: translate instructions
    next_variable = 16
    machine_code = []

    for line_no, line in lines:
        if line.startswith("(") and line.endswith(")"):
            continue

        if line.startswith("@"):
            value = line[1:].strip()

            if value.isdigit():
                address = int(value)
            else:
                if value not in symbols:
                    symbols[value] = next_variable
                    next_variable += 1
                address = symbols[value]

            if not 0 <= address <= 32767:
                raise ValueError(f"Line {line_no}: A-instruction address out of range")

            machine_code.append(format(address, "016b"))

        else:
            if ";" in line:
                instruction, jump_part = line.split(";", 1)
            else:
                instruction, jump_part = line, ""

            if "=" in instruction:
                dest_part, comp_part = instruction.split("=", 1)
            else:
                dest_part, comp_part = "", instruction

            dest_part = dest_part.strip()
            comp_part = comp_part.strip()
            jump_part = jump_part.strip()

            if comp_part not in comp:
                raise ValueError(f"Line {line_no}: Invalid comp: {comp_part}")
            if dest_part not in dest:
                raise ValueError(f"Line {line_no}: Invalid dest: {dest_part}")
            if jump_part not in jump:
                raise ValueError(f"Line {line_no}: Invalid jump: {jump_part}")

            machine_code.append(
                "111" + comp[comp_part] + dest[dest_part] + jump[jump_part]
            )

    output_path = path.with_suffix(".hack")
    output_path.write_text("\n".join(machine_code) + "\n", encoding="utf-8")
    print(f"Assembly successful! Output: {output_path}")
    print(f"Total instructions: {len(machine_code)}")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    else:
        input_file = input("Enter ASM file path: ").strip().strip('"')

    try:
        assemble(input_file)
    except Exception as error:
        print("Assembler error:", error)
